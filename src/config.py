import os
import sys
import urllib.request
import zipfile
import shutil
import logging 

class Config:
    def __init__(self):

        # === Percorsi e directory ===

        self.host = '127.0.0.1'
        self.port = 5000

        if getattr(sys, 'frozen', False):
            # Se eseguito come exe PyInstaller
            self.BASE_DIR = os.path.dirname(sys.executable)
        else:
            self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        self.TEMPLATE_DIR = self.resource_path('templates')
        self.STATIC_DIR = self.resource_path('static')
        self.FFMPEG_PATH = self.resource_path('ffmpeg.exe')

        self.DOWNLOAD_DIR = os.path.join(self.BASE_DIR, 'download')
        self.FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        self.FFMPEG_ZIP_PATH = os.path.join(self.BASE_DIR, 'ffmpeg.zip')
        self.FFMPEG_EXTRACT_DIR = os.path.join(self.BASE_DIR, 'ffmpeg_tmp')
        self.DATA_PATH = os.path.join(os.path.dirname(sys.executable), "data.json")
        self.BASE_URL = f'http://{self.host}:{self.port}'
        self.APP_NAME = 'StefyTube'
        self.LOG_PATH = 'log.log'
        self.MERGE_DIR = os.path.join(self.BASE_DIR, 'merge')

        # === Crea le cartelle se non esistono ===

        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(self.MERGE_DIR, exist_ok=True)

        # === Logging ===

        self.logger = logging.getLogger('werkzeug')  # logger delle richieste HTTP
        self.logger.setLevel(logging.INFO)

        # Handler per il terminale (console)
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.INFO)
        self.console_formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        self.console_handler.setFormatter(self.console_formatter)
        
        # Handler per il file
        self.file_handler = logging.FileHandler(self.LOG_PATH)
        self.file_handler.setLevel(logging.INFO)
        self.file_formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        self.file_handler.setFormatter(self.file_formatter)

        # Aggiungi gli handler al logger
        self.logger.addHandler(self.console_handler)
        self.logger.addHandler(self.file_handler)

        # === ffmpeg.exe Dependency
        
        if not os.path.exists(self.FFMPEG_PATH):
            os.makedirs(self.FFMPEG_EXTRACT_DIR, exist_ok=True) 
            urllib.request.urlretrieve(self.FFMPEG_URL, self.FFMPEG_ZIP_PATH)
            with zipfile.ZipFile(self.FFMPEG_ZIP_PATH, 'r') as zip_ref:
                zip_ref.extractall(self.FFMPEG_EXTRACT_DIR)

            ffmpeg_path = None
            for root, dirs, files in os.walk(self.FFMPEG_EXTRACT_DIR):
                if self.FFMPEG_PATH in files:
                    ffmpeg_path = os.path.join(root, self.FFMPEG_PATH)
                    shutil.copy(ffmpeg_path, self.FFMPEG_PATH)
                    break

            os.remove(self.FFMPEG_ZIP_PATH)
            shutil.rmtree(self.FFMPEG_EXTRACT_DIR, ignore_errors=True)  

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)