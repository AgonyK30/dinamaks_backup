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

# Modern ve profesyonel renk teması
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DinaMaksUltimate(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- PENCERE AYARLARI ---
        self.title("dinaMAKS Veritabanı Koruyucu v5.0 - Enterprise")
        self.geometry("1150x850")
        self.minsize(900, 700)
        self.config_path = "ayarlar.json"
        self.db_mgr = DBManager()
        self.db_checks = {}

        # --- ANA DEĞİŞKENLER ---
        self.servis_adi = "DinaMaksBackupService"
        self.menu_buttons = {}
        self.current_page = None
        
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
        
        # İlk sayfayı aç
        self.show_page("sql")

    def setup_sidebar(self):
        """Sol taraftaki modern navigasyon paneli"""
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=("gray90", "gray13"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1) # Menü ile alt bilgi arasına boşluk
        
        # Logo ve Başlık
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(40, 30), padx=20, sticky="ew")
        
        ctk.CTkLabel(logo_frame, text="dinaMAKS", font=ctk.CTkFont(size=28, weight="bold"), text_color="#3b82f6").pack()
        ctk.CTkLabel(logo_frame, text="Enterprise Edition", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack()

        # Menü Butonları ve İkonlar
        menu_items = [
            ("💾  SQL & Veritabanı", "sql"),
            ("☁️  Bulut (FTP)", "ftp"),
            ("📧  E-Posta Raporu", "mail"),
            ("⚙️  Otomasyon & Servis", "sched"),
            ("📜  Sistem Günlükleri", "logs")
        ]

        for i, (text, page) in enumerate(menu_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=text, height=45, fg_color="transparent", 
                anchor="w", hover_color=("#e2e8f0", "#1e293b"),
                font=ctk.CTkFont(size=14, weight="bold"), text_color=("gray10", "gray90"),
                command=lambda p=page: self.show_page(p)
            )
            btn.grid(row=i, column=0, pady=5, padx=15, sticky="ew")
            self.menu_buttons[page] = btn

        # Alt Bilgi / Servis Durumu
        status_frame = ctk.CTkFrame(self.sidebar, fg_color=("gray85", "gray17"), corner_radius=8)
        status_frame.grid(row=7, column=0, pady=20, padx=15, sticky="ew")
        
        ctk.CTkLabel(status_frame, text="Servis Durumu", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(10, 0))
        self.status_indicator = ctk.CTkLabel(status_frame, text="Kontrol Ediliyor...", text_color="#f59e0b", font=ctk.CTkFont(size=13, weight="bold"))
        self.status_indicator.pack(pady=(0, 10))

    def create_input_group(self, parent, label_text, placeholder, is_password=False):
        """Label ve Entry'yi modern bir şekilde gruplayan yardımcı fonksiyon"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        # Şık etiket
        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=("gray30", "gray70")).pack(anchor="w", padx=2, pady=(0, 2))
        
        # Giriş alanı
        ent = ctk.CTkEntry(frame, placeholder_text=placeholder, height=40, corner_radius=6, border_width=1)
        if is_password: 
            ent.configure(show="•")
        ent.pack(fill="x", expand=True)
        return frame, ent

    def setup_content_area(self):
        """Sağ taraftaki içerik sayfaları - Kart tasarımları ile"""
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, padx=40, pady=40, sticky="nsew")

        self.pages = {}

        # -------------------------------------------------------------
        # 1. SQL SAYFASI
        # -------------------------------------------------------------
        p_sql = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(p_sql, text="SQL Sunucu Yapılandırması", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        # Bağlantı Kartı
        card_sql = ctk.CTkFrame(p_sql, fg_color=("gray90", "gray13"), corner_radius=10)
        card_sql.pack(fill="x", pady=(0, 20), ipady=15, ipadx=15)
        
        _, self.ent_server = self.create_input_group(card_sql, "Sunucu Adresi", "Örn: .\\SQLEXPRESS veya 192.168.1.100")
        self.ent_server.master.pack(fill="x", pady=5)
        
        # Kullanıcı ve Şifreyi yan yana koyalım
        sql_cred_frame = ctk.CTkFrame(card_sql, fg_color="transparent")
        sql_cred_frame.pack(fill="x", pady=5)
        sql_cred_frame.grid_columnconfigure((0, 1), weight=1)
        
        _, self.ent_sql_user = self.create_input_group(sql_cred_frame, "SQL Kullanıcı Adı", "Windows Auth için boş bırakın")
        self.ent_sql_user.master.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        _, self.ent_sql_pass = self.create_input_group(sql_cred_frame, "SQL Şifresi", "••••••••", is_password=True)
        self.ent_sql_pass.master.grid(row=0, column=1, padx=(10, 0), sticky="ew")

        ctk.CTkButton(card_sql, text="Bağlantıyı Sına & Listeyi Güncelle", font=ctk.CTkFont(weight="bold"), fg_color="#2563eb", hover_color="#1d4ed8", height=45, command=self.handle_sql_connect).pack(pady=(20, 5), fill="x")
        
        # Veritabanı Listesi Kartı
        self.db_list_container = ctk.CTkScrollableFrame(p_sql, label_text="Yedeklenecek Veritabanlarını Seçin", label_font=ctk.CTkFont(size=14, weight="bold"), fg_color=("gray90", "gray13"))
        self.db_list_container.pack(fill="both", expand=True)
        self.pages["sql"] = p_sql

        # -------------------------------------------------------------
        # 2. FTP SAYFASI
        # -------------------------------------------------------------
        p_ftp = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(p_ftp, text="Bulut (FTP) Yedekleme Ayarları", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        card_ftp = ctk.CTkFrame(p_ftp, fg_color=("gray90", "gray13"), corner_radius=10)
        card_ftp.pack(fill="x", ipady=15, ipadx=15)

        _, self.ent_ftp_host = self.create_input_group(card_ftp, "FTP Sunucu Adresi", "Örn: ftp.sirketiniz.com")
        self.ent_ftp_host.master.pack(fill="x", pady=10)
        
        _, self.ent_ftp_user = self.create_input_group(card_ftp, "FTP Kullanıcı Adı", "Kullanıcı adınızı girin")
        self.ent_ftp_user.master.pack(fill="x", pady=10)
        
        _, self.ent_ftp_pass = self.create_input_group(card_ftp, "FTP Şifresi", "••••••••", is_password=True)
        self.ent_ftp_pass.master.pack(fill="x", pady=10)
        self.pages["ftp"] = p_ftp

        # -------------------------------------------------------------
        # 3. MAIL SAYFASI
        # -------------------------------------------------------------
        p_mail = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(p_mail, text="E-Posta Raporlama Bildirimleri", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        card_mail = ctk.CTkFrame(p_mail, fg_color=("gray90", "gray13"), corner_radius=10)
        card_mail.pack(fill="x", ipady=15, ipadx=15)

        _, self.ent_mail_from = self.create_input_group(card_mail, "Gönderen E-Posta Adresi", "Örn: dinamikotomasyon@otomasyon.com")
        self.ent_mail_from.master.pack(fill="x", pady=10)
        
        _, self.ent_mail_pass = self.create_input_group(card_mail, "Uygulama Şifresi (App Password)", "••••••••", is_password=True)
        self.ent_mail_pass.master.pack(fill="x", pady=10)
        
        _, self.ent_mail_to = self.create_input_group(card_mail, "Raporların Gideceği Alıcı", "Örn: admin@sirket.com")
        self.ent_mail_to.master.pack(fill="x", pady=10)
        self.pages["mail"] = p_mail

        # -------------------------------------------------------------
        # 4. ZAMANLAMA & SERVİS SAYFASI
        # -------------------------------------------------------------
        p_sched = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(p_sched, text="Otomasyon ve Windows Servis Yönetimi", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        # Ayarlar Kartı
        card_sched = ctk.CTkFrame(p_sched, fg_color=("gray90", "gray13"), corner_radius=10)
        card_sched.pack(fill="x", pady=(0, 20), ipady=15, ipadx=15)
        
        _, self.ent_time = self.create_input_group(card_sched, "Günlük Yedekleme Saati (HH:MM)", "Örn: 03:00")
        self.ent_time.master.pack(fill="x", pady=10)
        
        ctk.CTkButton(card_sched, text="Tüm Yapılandırmayı Kaydet", font=ctk.CTkFont(weight="bold"), fg_color="#10b981", hover_color="#059669", height=45, command=self.save_config).pack(pady=(15, 5), fill="x")

        # Servis Aksiyonları Kartı
        card_actions = ctk.CTkFrame(p_sched, fg_color=("gray90", "gray13"), corner_radius=10)
        card_actions.pack(fill="x", ipady=15, ipadx=15)
        
        ctk.CTkLabel(card_actions, text="Servis Aksiyonları", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(0, 10))

        action_grid = ctk.CTkFrame(card_actions, fg_color="transparent")
        action_grid.pack(fill="x")
        action_grid.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(action_grid, text="Servisi Kur / Güncelle", fg_color="#475569", hover_color="#334155", height=40, command=self.manage_service_install).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")
        self.btn_servis_start = ctk.CTkButton(action_grid, text="Servisi Başlat / Durdur", fg_color="#2563eb", hover_color="#1d4ed8", height=40, command=lambda: self.service_control("start"))
        self.btn_servis_start.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")

        ctk.CTkButton(card_actions, text="Şimdi Manuel Yedekleme Başlat", font=ctk.CTkFont(weight="bold"), fg_color="#f59e0b", hover_color="#d97706", height=45, command=self.manual_backup_trigger).pack(pady=(15, 0), fill="x")

        self.pages["sched"] = p_sched

        # -------------------------------------------------------------
        # 5. LOG SAYFASI
        # -------------------------------------------------------------
        p_logs = ctk.CTkFrame(self.container, fg_color="transparent")
        
        log_header = ctk.CTkFrame(p_logs, fg_color="transparent")
        log_header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(log_header, text="Sistem Günlükleri", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkButton(log_header, text="Logları Yenile", width=120, height=35, command=self.refresh_logs).pack(side="right")
        
        self.log_text = ctk.CTkTextbox(p_logs, font=ctk.CTkFont(family="Consolas", size=13), fg_color=("gray90", "gray13"), border_width=1)
        self.log_text.pack(fill="both", expand=True)
        self.pages["logs"] = p_logs

    def show_page(self, name):
        """Sayfalar arası geçiş ve aktif buton stili yönetimi"""
        # Aktif butonu vurgula, diğerlerini sıfırla
        for key, btn in self.menu_buttons.items():
            if key == name:
                btn.configure(fg_color=("#cbd5e1", "#334155")) # Aktif arka plan
            else:
                btn.configure(fg_color="transparent")

        # Mevcut sayfayı gizle, yenisini göster
        for p in self.pages.values(): 
            p.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        self.current_page = name

        # Log sayfasına geçiliyorsa otomatik yenile
        if name == "logs":
            self.refresh_logs()

    # --- MANTIK VE VERİ İŞLEMLERİ (Aynı Kaldı) ---

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
                cb = ctk.CTkCheckBox(self.db_list_container, text=db, variable=var, font=ctk.CTkFont(size=13))
                cb.pack(anchor="w", padx=20, pady=8)
                self.db_checks[db] = var
            messagebox.showinfo("Başarılı", f"{len(dbs)} Veritabanı başarıyla listelendi.")
            logging.info("SQL Bağlantısı başarılı.")
        else:
            messagebox.showerror("Bağlantı Hatası", "SQL Sunucusuna bağlanılamadı. Bilgileri kontrol edin.")
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
            messagebox.showinfo("Başarılı", "Tüm sistem ayarları başarıyla kaydedildi.")
            logging.info("Ayarlar JSON dosyasına yazıldı.")
        except Exception as e:
            logging.error(f"Kayıt hatası: {e}")
            messagebox.showerror("Hata", "Ayarlar kaydedilirken bir sorun oluştu.")

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
                self.status_indicator.configure(text="🟢 Çalışıyor", text_color="#10b981")
            else:
                self.status_indicator.configure(text="🔴 Durduruldu", text_color="#ef4444")
        except:
            self.status_indicator.configure(text="⚪ Kurulu Değil", text_color="gray")

    def manage_service_install(self):
        script_path = os.path.abspath("arka_plan_servisi.py")
        try:
            subprocess.run([sys.executable, script_path, "install"], check=True)
            subprocess.run(["sc", "config", self.servis_adi, "start=", "auto"], check=True)
            messagebox.showinfo("Servis", "Servis başarıyla Windows'a kaydedildi.")
            self.check_service_status()
        except Exception as e:
            messagebox.showerror("Yetki Hatası", "Servis kurulumu için programı Yönetici (Administrator) olarak çalıştırmanız gerekebilir.")

    def service_control(self, action):
        cmd = "start" if action == "start" else "stop"
        try:
            subprocess.run(["net", cmd, self.servis_adi], check=True)
            self.check_service_status()
        except:
            messagebox.showerror("Hata", f"Servis {action} işlemi başarısız. Yönetici izinlerini kontrol edin.")

    # --- MANUEL İŞLEMLER ---

    def manual_backup_trigger(self):
        secili = [db for db, var in self.db_checks.items() if var.get()]
        if not secili: 
            return messagebox.showwarning("Eksik Seçim", "Lütfen SQL sekmesinden en az bir veritabanı seçin!")
        
        threading.Thread(target=self.run_manual_backup, args=(secili,), daemon=True).start()

    def run_manual_backup(self, dbs):
        logging.info("Manuel yedekleme başlatıldı.")
        engine = BackupEngine(self.db_mgr)
        for db in dbs:
            engine.execute_backup(db)
        messagebox.showinfo("İşlem Tamam", "Yedekleme görevleri tamamlandı. Detaylar için logları kontrol edin.")
        logging.info("Manuel yedekleme başarıyla bitti.")

    def refresh_logs(self):
        if os.path.exists("dinamaks_system.log"):
            with open("dinamaks_system.log", "r", encoding="utf-8") as f:
                self.log_text.delete("1.0", "end")
                self.log_text.insert("1.0", f.read())
                self.log_text.see("end") # Otomatik en aşağı kaydır

if __name__ == "__main__":
    app = DinaMaksUltimate()
    app.mainloop()
