import logging
import os
import sys
from datetime import datetime

def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M") + "_SQL_Backup.log"
    log_path = os.path.join("logs", log_filename)

    logger = logging.getLogger("SQLBackupManager")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

logger = setup_logger()