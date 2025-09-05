import os
import sys
import urllib.request
import zipfile
import shutil

class Config:
    def __init__(self):

        # === Percorsi e directory ===

        self.host = '127.0.0.1'
        self.port = 5000
        self.BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.TEMPLATE_DIR = os.path.join(self.BASE_DIR, 'templates')
        self.DOWNLOAD_DIR = os.path.join(self.BASE_DIR, 'download')
        self.FFMPEG_PATH = os.path.join(self.BASE_DIR, 'ffmpeg.exe')
        self.FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        self.FFMPEG_ZIP_PATH = os.path.join(self.BASE_DIR, 'ffmpeg.zip')
        self.FFMPEG_EXTRACT_DIR = os.path.join(self.BASE_DIR, 'ffmpeg_tmp')
        self.DATA_PATH = os.path.join(self.BASE_DIR, 'data.json')
        self.BASE_URL = f'http://{self.host}:{self.port}'
        self.APP_NAME = 'StefyTube'

        # === Crea le cartelle se non esistono ===

        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)

        # === Logging su file ===
        
        self.log_path = 'log.log'
        sys.stdout = open(self.log_path, 'w')
        sys.stderr = open(self.log_path, 'w')

        # === ffmpeg.exe Dependency
        
        if not os.path.exists(self.FFMPEG_PATH):
            os.makedirs(self.FFMPEG_EXTRACT_DIR, exist_ok=True) 
            urllib.request.urlretrieve(self.FFMPEG_URL, self.FFMPEG_ZIP_PATH)
            with zipfile.ZipFile(self.FFMPEG_ZIP_PATH, 'r') as zip_ref:
                zip_ref.extractall(self.FFMPEG_EXTRACT_DIR)

            ffmpeg_path = None
            for root, dirs, files in os.walk(self.FFMPEG_EXTRACT_DIR):
                if "ffmpeg.exe" in files:
                    ffmpeg_path = os.path.join(root, "ffmpeg.exe")
                    shutil.copy(ffmpeg_path, self.FFMPEG_PATH)
                    break

            os.remove(self.FFMPEG_ZIP_PATH)
            shutil.rmtree(self.FFMPEG_EXTRACT_DIR, ignore_errors=True)  