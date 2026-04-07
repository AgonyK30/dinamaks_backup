import time
import schedule
import json
import os
from datetime import datetime
from core.db import DBManager
from core.backup import BackupEngine
from core.ftp import FTPManager

def job():
    if not os.path.exists("config.json"): return
    with open("config.json", "r") as f:
        config = json.load(f)
    
    print(f"[{datetime.now()}] Zamanlanmış yedekleme başladı...")
    db_mgr = DBManager()
    if db_mgr.connect(config['sql_server'], config['sql_user'], config['sql_pass']):
        engine = BackupEngine(db_mgr)
        targets = db_mgr.get_databases() if config['all_dbs'] else config['selected_dbs']
        
        for db in targets:
            path = engine.execute_backup(db, config['path'])
            if path and config['ftp_use']:
                ftp = FTPManager(config['ftp_host'], config['ftp_user'], config['ftp_pass'])
                ftp.upload_backup(path)
    # Burada e-posta gönderim fonksiyonu tetiklenebilir

def run_service():
    # settings'den saati oku (Örn: "03:00")
    schedule.every().day.at("03:00").do(job) 
    while True:
        schedule.run_pending()
        time.sleep(60)