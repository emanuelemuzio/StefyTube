import os 
import yt_dlp
import platform
import subprocess
from flask import jsonify
from .config import Config
from .data import Data, Entry, EntryResponse
from .requests import DownloadRequest

# === Funzioni core e di utility di download ===

class Service:

    config : Config

    def __init__(self, config : Config):
        self.config = config

    def download_video(self, request : DownloadRequest, data : Data):

        entry = Entry(url=request.url, format=request.format, noplaylist=request.noplaylist)
        data.add_to_queue(entry)

    def download_entry(self, entry: Entry): 
        completed_entries = []

        def hook(d): 
            if d["status"] == "downloading": 
                total = d.get("total_bytes") or d.get("total_bytes_estimate") 
                downloaded = d.get("downloaded_bytes", 0) 
                if total: 
                    entry.progress = int(downloaded / total * 100) 
                    entry.status = "downloading" 
            elif d["status"] == "finished": 
                entry.status = "completed" 
                # aggiorna il filepath con quello effettivo dopo conversione 
                entry.filepath = d.get("filename") or entry.filepath 

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
                "outtmpl" : outtmpl,
                "noplaylist": entry.noplaylist
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

                # playlist o singolo video
                if "entries" in info:
                    for video_info in info["entries"]:
                        e = Entry(
                            id=video_info.get("id"),
                            url=video_info.get("webpage_url"),
                            title=video_info.get("title"),
                            filepath=ydl.prepare_filename(video_info),
                            format=entry.format,
                            status="completed"
                        )
                        if entry.format == "mp3":
                            e.filepath = os.path.splitext(e.filepath)[0] + ".mp3"
                        completed_entries.append(e)
                else:
                    entry.id = info.get("id")
                    entry.title = info.get("title")
                    entry.filepath = ydl.prepare_filename(info)
                    if entry.format == "mp3":
                        entry.filepath = os.path.splitext(entry.filepath)[0] + ".mp3"
                    entry.status = "completed"
                    completed_entries.append(entry)

        except Exception:
            entry.status = "failed"
            completed_entries.append(entry)

        return completed_entries

    def retrieve_history(self, data):
        history_list = [EntryResponse.serializable_from_entry(e) for e in data.history]
        return history_list
    
    def retrieve_queue(self, data):
        queue_list = [EntryResponse.serializable_from_entry(e) for e in data.queue]
        return queue_list
    
    def open_downloads(self):
        download_path = os.path.join(os.getcwd(), self.config.DOWNLOAD_DIR)

        try:
            if platform.system() == 'Windows':
                os.startfile(download_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', download_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', download_path])
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})