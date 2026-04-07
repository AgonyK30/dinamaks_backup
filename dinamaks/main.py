import customtkinter as ctk
import json
import os
import threading
import subprocess
import sys
import logging
from datetime import datetime
from tkinter import messagebox, filedialog
from core.db import DBManager
from core.backup import BackupEngine

# --- LOG SİSTEMİ KURULUMU ---
logging.basicConfig(
    filename='dinamaks_system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DinaMaksUltimate(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- PENCERE AYARLARI ---
        self.title("dinaMAKS Veritabanı Koruyucu v5.0 - Enterprise")
        self.geometry("1100x850")
        self.config_path = "ayarlar.json"
        self.db_mgr = DBManager()
        self.db_checks = {}

        # --- ANA DEĞİŞKENLER ---
        self.servis_adi = "DinaMaksBackupService"
        
        # --- UI LAYOUT ---
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # İçerik
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_content_area()
        
        # Başlangıç İşlemleri
        self.load_config()
        self.check_service_status()
        logging.info("Uygulama başlatıldı.")

    def setup_sidebar(self):
        """Sol taraftaki navigasyon paneli"""
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Logo ve Başlık
        ctk.CTkLabel(self.sidebar, text="dinaMAKS", font=ctk.CTkFont(size=28, weight="bold"), text_color="#3b82f6").pack(pady=(30, 10))
        ctk.CTkLabel(self.sidebar, text="Enterprise Edition", font=ctk.CTkFont(size=12)).pack(pady=(0, 30))

        # Menü Butonları
        menu_items = [
            ("SQL & Veritabanı", "sql"),
            ("Bulut (FTP) Ayarları", "ftp"),
            ("E-Posta Raporu", "mail"),
            ("Zamanlama & Servis", "sched"),
            ("Sistem Günlükleri", "logs")
        ]

        for text, page in menu_items:
            btn = ctk.CTkButton(
                self.sidebar, text=text, height=45, fg_color="transparent", 
                anchor="w", hover_color="#1e293b",
                command=lambda p=page: self.show_page(p)
            )
            btn.pack(pady=5, padx=20, fill="x")

        # Alt Bilgi
        self.status_indicator = ctk.CTkLabel(self.sidebar, text="Servis: Kontrol Ediliyor...", text_color="orange")
        self.status_indicator.pack(side="bottom", pady=20)

    def setup_content_area(self):
        """Sağ taraftaki içerik sayfaları"""
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, padx=30, pady=30, sticky="nsew")

        self.pages = {}

        # 1. SQL SAYFASI
        p_sql = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(p_sql, text="1. SQL Sunucu Bağlantısı", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10, anchor="w")
        
        self.ent_server = self.create_input(p_sql, "Sunucu Adresi (Örn: .\\SQLEXPRESS)")
        self.ent_sql_user = self.create_input(p_sql, "Kullanıcı Adı (Windows Auth için boş bırak)")
        self.ent_sql_pass = self.create_input(p_sql, "Şifre", is_password=True)
        
        ctk.CTkButton(p_sql, text="SUNUCUYA BAĞLAN VE LİSTEYİ GÜNCELLE", fg_color="#2563eb", height=45, command=self.handle_sql_connect).pack(pady=20, fill="x")
        
        self.db_list_container = ctk.CTkScrollableFrame(p_sql, height=350, label_text="Yedeklenecek Veritabanları")
        self.db_list_container.pack(fill="both", expand=True, pady=10)
        self.pages["sql"] = p_sql

        # 2. FTP SAYFASI
        p_ftp = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(p_ftp, text="2. FTP / Bulut Ayarları (Opsiyonel)", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10, anchor="w")
        self.ent_ftp_host = self.create_input(p_ftp, "FTP Adresi (ftp.siteniz.com)")
        self.ent_ftp_user = self.create_input(p_ftp, "FTP Kullanıcı")
        self.ent_ftp_pass = self.create_input(p_ftp, "FTP Şifre", is_password=True)
        self.pages["ftp"] = p_ftp

        # 3. MAIL SAYFASI
        p_mail = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(p_mail, text="3. E-Posta Raporlama", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10, anchor="w")
        self.ent_mail_from = self.create_input(p_mail, "Gönderen E-Posta")
        self.ent_mail_pass = self.create_input(p_mail, "E-Posta Uygulama Şifresi", is_password=True)
        self.ent_mail_to = self.create_input(p_mail, "Alıcı E-Posta")
        self.pages["mail"] = p_mail

        # 4. ZAMANLAMA & SERVİS SAYFASI
        p_sched = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(p_sched, text="4. Otomasyon Ayarları", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10, anchor="w")
        self.ent_time = self.create_input(p_sched, "Yedekleme Saati (Örn: 03:00)")
        
        ctk.CTkButton(p_sched, text="TÜM AYARLARI KAYDET", fg_color="#10b981", height=50, command=self.save_config).pack(pady=10, fill="x")
        ctk.CTkButton(p_sched, text="SERVİSİ WİNDOWS'A KUR / GÜNCELLE", fg_color="#334155", height=50, command=self.manage_service_install).pack(pady=5, fill="x")
        
        self.btn_servis_start = ctk.CTkButton(p_sched, text="SERVİSİ BAŞLAT", fg_color="#2563eb", command=lambda: self.service_control("start"))
        self.btn_servis_start.pack(pady=5, fill="x")
        
        ctk.CTkButton(p_sched, text="ŞİMDİ MANUEL YEDEK AL", fg_color="#f59e0b", height=50, command=self.manual_backup_trigger).pack(pady=20, fill="x")
        self.pages["sched"] = p_sched

        # 5. LOG SAYFASI
        p_logs = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(p_logs, text="5. Sistem Günlükleri", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10, anchor="w")
        self.log_text = ctk.CTkTextbox(p_logs, height=500)
        self.log_text.pack(fill="both", expand=True)
        ctk.CTkButton(p_logs, text="LOGLARI YENİLE", command=self.refresh_logs).pack(pady=10)
        self.pages["logs"] = p_logs

    def create_input(self, master, placeholder, is_password=False):
        ent = ctk.CTkEntry(master, placeholder_text=placeholder, width=500, height=45)
        if is_password: ent.configure(show="*")
        ent.pack(pady=10)
        return ent

    def show_page(self, name):
        for p in self.pages.values(): p.pack_forget()
        self.pages[name].pack(fill="both", expand=True)

    # --- MANTIK VE VERİ İŞLEMLERİ ---

    def handle_sql_connect(self):
        server = self.ent_server.get()
        user = self.ent_sql_user.get() if self.ent_sql_user.get() else None
        pwd = self.ent_sql_pass.get() if self.ent_sql_pass.get() else None
        
        if self.db_mgr.connect(server, user, pwd):
            for w in self.db_list_container.winfo_children(): w.destroy()
            self.db_checks = {}
            dbs = self.db_mgr.get_databases()
            for db in dbs:
                var = ctk.BooleanVar()
                cb = ctk.CTkCheckBox(self.db_list_container, text=db, variable=var)
                cb.pack(anchor="w", padx=20, pady=5)
                self.db_checks[db] = var
            messagebox.showinfo("Başarılı", f"{len(dbs)} Veritabanı listelendi.")
            logging.info("SQL Bağlantısı başarılı.")
        else:
            messagebox.showerror("Hata", "SQL Sunucusuna bağlanılamadı.")
            logging.error("SQL Bağlantı hatası.")

    def save_config(self):
        secili_dbs = [db for db, var in self.db_checks.items() if var.get()]
        data = {
            "sql_server": self.ent_server.get(),
            "sql_user": self.ent_sql_user.get(),
            "sql_pass": self.ent_sql_pass.get(),
            "ftp_host": self.ent_ftp_host.get(),
            "ftp_user": self.ent_ftp_user.get(),
            "ftp_pass": self.ent_ftp_pass.get(),
            "mail_from": self.ent_mail_from.get(),
            "mail_pass": self.ent_mail_pass.get(),
            "mail_to": self.ent_mail_to.get(),
            "saat": self.ent_time.get(),
            "veritabanlari": secili_dbs
        }
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Sistem", "Ayarlar başarıyla kaydedildi.")
            logging.info("Ayarlar JSON dosyasına yazıldı.")
        except Exception as e:
            logging.error(f"Kayıt hatası: {e}")

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                c = json.load(f)
                self.ent_server.insert(0, c.get("sql_server", ""))
                self.ent_ftp_host.insert(0, c.get("ftp_host", ""))
                self.ent_mail_to.insert(0, c.get("mail_to", ""))
                self.ent_time.insert(0, c.get("saat", "03:00"))

    # --- SERVİS YÖNETİMİ ---

    def check_service_status(self):
        try:
            output = subprocess.check_output(f'sc query {self.servis_adi}', shell=True).decode()
            if "RUNNING" in output:
                self.status_indicator.configure(text="Servis: ÇALIŞIYOR", text_color="#10b981")
            else:
                self.status_indicator.configure(text="Servis: DURDURULDU", text_color="#ef4444")
        except:
            self.status_indicator.configure(text="Servis: KURULU DEĞİL", text_color="gray")

    def manage_service_install(self):
        script_path = os.path.abspath("arka_plan_servisi.py")
        try:
            subprocess.run([sys.executable, script_path, "install"], check=True)
            subprocess.run(["sc", "config", self.servis_adi, "start=", "auto"], check=True)
            messagebox.showinfo("Servis", "Servis başarıyla Windows'a kaydedildi.")
            self.check_service_status()
        except Exception as e:
            messagebox.showerror("Hata", "Servis kurulumu için yönetici izni gerekebilir.")

    def service_control(self, action):
        cmd = "start" if action == "start" else "stop"
        try:
            subprocess.run(["net", cmd, self.servis_adi], check=True)
            self.check_service_status()
        except:
            messagebox.showerror("Hata", f"Servis {action} işlemi başarısız.")

    # --- MANUEL İŞLEMLER ---

    def manual_backup_trigger(self):
        secili = [db for db, var in self.db_checks.items() if var.get()]
        if not secili: return messagebox.showwarning("Uyarı", "DB Seçin!")
        
        threading.Thread(target=self.run_manual_backup, args=(secili,), daemon=True).start()

    def run_manual_backup(self, dbs):
        logging.info("Manuel yedekleme başlatıldı.")
        engine = BackupEngine(self.db_mgr)
        for db in dbs:
            engine.execute_backup(db)
        messagebox.showinfo("Bitti", "Yedekleme tamamlandı. Logları kontrol edin.")
        logging.info("Manuel yedekleme başarıyla bitti.")

    def refresh_logs(self):
        if os.path.exists("dinamaks_system.log"):
            with open("dinamaks_system.log", "r") as f:
                self.log_text.delete("1.0", "end")
                self.log_text.insert("1.0", f.read())

if __name__ == "__main__":
    app = DinaMaksUltimate()
    app.mainloop()