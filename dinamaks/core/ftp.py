import ftplib
import os

class FTPManager:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    def upload_backup(self, file_path):
        try:
            filename = os.path.basename(file_path)
            with ftplib.FTP(self.host) as ftp:
                ftp.login(self.user, self.password)
                with open(file_path, "rb") as file:
                    ftp.storbinary(f"STOR {filename}", file)
                return True
        except:
            return False