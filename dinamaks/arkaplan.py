import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import time
import json
from core.db import DBManager
from core.backup import BackupEngine

class DinaMaksService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DinaMaksBackupService"
    _svc_display_name_ = "dinaMAKS Veritabanı Yedekleme Servisi"
    _svc_description_ = "SQL yedeklerini otomatik alan enterprise servis."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        # Servis başladığında Windows'a haber ver
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        # Burası ana döngü. Uygulama burada yaşar.
        while self.is_alive:
            try:
                # AYARLARI OKU (Dosya yoluna dikkat: Servisler System32'de çalışır!)
                # Bu yüzden tam yol (absolute path) kullanmalıyız.
                script_dir = os.path.dirname(os.path.abspath(__file__))
                config_path = os.path.join(script_dir, "ayarlar.json")

                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    
                    simdi = time.strftime("%H:%M")
                    if simdi == config.get("saat", "03:00"):
                        # Yedekleme işlemini başlat
                        self.execute_backup_task(config)
                        time.sleep(65) # Aynı dakika iki kez çalışmasın
            except Exception as e:
                # Hata olursa log dosyasına yaz ki neden başlamadığını görelim
                with open("servis_hata.log", "a") as f:
                    f.write(f"Hata: {str(e)}\n")
            
            # Windows'u yormamak için 30 saniyede bir kontrol et
            time.sleep(30)

    def execute_backup_task(self, config):
        db_mgr = DBManager()
        if db_mgr.connect(config['sql_server'], config.get('sql_user'), config.get('sql_pass')):
            engine = BackupEngine(db_mgr)
            for db in config.get('veritabanlari', []):
                engine.execute_backup(db)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        win32serviceutil.HandleCommandLine(DinaMaksService)
    else:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(DinaMaksService)
        servicemanager.StartServiceCtrlDispatcher()