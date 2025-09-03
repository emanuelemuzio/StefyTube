import os 
import yt_dlp
from .config import Config
from .data import Data, Entry
from .requests import DownloadRequest

# === Funzioni core e di utility di download ===

class Service:

    config : Config

    def __init__(self, config : Config):
        self.config = config

    def download_video(self, request : DownloadRequest, data : Data):

        entry = Entry(url=request.url, format=request.format, noplaylist=request.noplaylist)
        data.add_to_queue(entry)

    def download_entry(self, entry: Entry, data: Data, save_path="data.json"): 
        def hook(d): 
            if d["status"] == "downloading": 
                total = d.get("total_bytes") or d.get("total_bytes_estimate") 
                downloaded = d.get("downloaded_bytes", 0) 
                if total: 
                    entry.progress = int(downloaded / total * 100) 
                    entry.status = "downloading" 
                    data.save(save_path) 
            elif d["status"] == "finished": 
                entry.status = "completed" 
                # aggiorna il filepath con quello effettivo dopo conversione 
                entry.filepath = d.get("filename") or entry.filepath 
                data.save(save_path) 

        outtmpl = os.path.join(self.config.DOWNLOAD_DIR, "%(title)s.%(ext)s")

        if entry.format == "mp3": 
            ydl_opts = { 
                "format": "bestaudio/best", 
                "postprocessors": [
                    { 
                        "key": "FFmpegExtractAudio", 
                        "preferredcodec": "mp3", 
                        "preferredquality": "192", 
                    }
                ], 
                "progress_hooks": [
                    hook
                ], 
                "quiet": True, 
                "outtmpl" : outtmpl
            } 
        else: 
            # mp4 
            ydl_opts = { 
                "format": "bestvideo+bestaudio/best", 
                "merge_output_format": "mkv", 
                "progress_hooks": [
                    hook
                ], 
                "quiet": True, 
                "outtmpl" : outtmpl, 
            } 
        try: 
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: 
                info = ydl.extract_info(entry.url, download=True) 
                entry.id = info.get("id") 
                entry.title = info.get("title") 
                # filepath finale corretto 
                entry.filepath = ydl.prepare_filename(info) 
                if entry.format == "mp3": 
                    # cambia estensione in .mp3 
                    entry.filepath = os.path.splitext(entry.filepath)[0] + ".mp3"
        except Exception: 
            entry.status = "failed"  

    def retrieve_history(self, data):
        history_list = [e.dict() for e in data.history]
        return history_list
    
    def retrieve_queue(self, data):
        queue_list = [e.dict() for e in data.queue]
        return queue_list