# config.py
import os
from datetime import timedelta

class Config:
    SECRET_KEY = '3054=HitM'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'user623'
    MYSQL_DB = 'data_beneficios'
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT =  False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    BACKUP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.BACKUP_FOLDER, exist_ok=True)