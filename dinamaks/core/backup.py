import os
from datetime import datetime

class BackupEngine:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def execute_backup(self, db_name, save_dir=r"C:\SQLBackups"):
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(save_dir, f"{db_name}_{timestamp}.bak")
        
        try:
            cursor = self.db_manager.connection.cursor()
            # SQL Server'a doğrudan komut gönderir
            cursor.execute(f"BACKUP DATABASE [{db_name}] TO DISK = '{file_path}' WITH FORMAT")
            while cursor.nextset(): pass
            return file_path
        except:
            return None