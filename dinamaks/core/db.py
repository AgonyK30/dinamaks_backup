import pyodbc
import winreg # Windows kayıt defterinden SQL servislerini bulmak için

class DBManager:
    def __init__(self):
        self.connection = None

    def discover_local_sql(self):
        """Windows Kayıt Defteri'ni tarayarak yüklü SQL Instance'larını bulur."""
        instances = []
        try:
            # SQL Server instance listesinin tutulduğu kayıt defteri yolu
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL")
            for i in range(winreg.QueryInfoKey(reg_key)[1]):
                name, value, _ = winreg.EnumValue(reg_key, i)
                instances.append(name)
        except:
            pass
        
        if not instances:
            return r".\SQLEXPRESS" # Hiç bulunamazsa standart olanı dön
        
        # Eğer MSSQLSERVER (Default) varsa sadece nokta (.) dön, yoksa .\AD şeklinde dön
        main_instance = instances[0]
        return "." if main_instance == "MSSQLSERVER" else rf".\{main_instance}"

    def connect(self, server, user=None, pwd=None):
        try:
            auth = f"UID={user};PWD={pwd};" if user and pwd else "Trusted_Connection=yes;"
            conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server};Database=master;{auth}Encrypt=no;TrustServerCertificate=yes;"
            self.connection = pyodbc.connect(conn_str, timeout=5)
            self.connection.autocommit = True
            return True
        except:
            return False

    def get_databases(self):
        if not self.connection: return []
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master','tempdb','model','msdb') AND state_desc = 'ONLINE'")
        return [row[0] for row in cursor]