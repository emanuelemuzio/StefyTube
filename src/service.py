import os 
import yt_dlp
import platform
import subprocess
from flask import jsonify
from .config import Config
from .data import Data, Entry, Merge
from .requests import DownloadRequest, HistoryDeleteRequest, QueueDeleteRequest, MergeUuidList, MergeDeleteRequest

class Service:

    config : Config

    def __init__(self, config : Config):
        self.config = config

    def log(self, msg : str):
        self.config.logger.log(msg)

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
                if entry.format == "mp3":
                    # sostituisci estensione con .mp3
                    entry.filepath = os.path.splitext(d.get("filename", entry.filepath))[0] + ".mp3"
                else:
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
                "noplaylist": entry.noplaylist,
                "ffmpeg_location": self.config.FFMPEG_PATH
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
                "noplaylist": entry.noplaylist,
                "ffmpeg_location": self.config.FFMPEG_PATH
            } 
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(entry.url, download=True)

                # playlist o singolo video
                entries_to_process = info.get("entries") or [info]
                for video_info in entries_to_process:
                    filepath_final = entry.filepath or video_info.get("_filename") or video_info.get("filepath") 
                    e = Entry(
                        id=video_info.get("id"),
                        url=video_info.get("webpage_url", entry.url),
                        title=video_info.get("title", entry.title),
                        filepath=filepath_final,
                        format=entry.format,
                        status="completed"
                    )
                    completed_entries.append(e)

        except Exception as e:
            self.log(str(e))
            entry.status = "failed"
            completed_entries.append(entry)

        return completed_entries

    def retrieve_history(self, data : Data):
        history_list = [e.serialize() for e in data.history]
        return history_list
    
    def retrieve_queue(self, data : Data):
        queue_list = [e.serialize() for e in data.queue]
        return queue_list
    
    def open_download_dir(self):
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
        
    def open_merge_dir(self):
        merge_path = os.path.join(os.getcwd(), self.config.MERGE_DIR)

        try:
            if platform.system() == 'Windows':
                os.startfile(merge_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', merge_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', merge_path])
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
        
    def delete_from_history(self, data : Data, request : HistoryDeleteRequest):
        data.remove_history_entry_by_uuid(request.uuid)

    def delete_from_queue(self, data : Data, request : QueueDeleteRequest):
        data.remove_queue_entry_by_uuid(request.uuid) 

    def delete_from_merge(self, data : Data, request : MergeDeleteRequest):
        data.remove_merge_by_uuid(request.uuid) 

    def merge_uuid_list(self, data : Data, request : MergeUuidList):
        uuids = request.uuids
        entries_to_merge = list(filter(lambda x : x.uuid in uuids, data.history))
        format_check_list = set(map(lambda x : x.format, entries_to_merge))
        output_format = None

        if len(entries_to_merge) != len(uuids):
            raise ValueError("UUIDs list mismatch")

        if len(format_check_list) > 1:
            raise ValueError("Format error")
        
        output_format = format_check_list.pop()
        filepaths = list(map(lambda x : x.filepath, entries_to_merge))
        title = request.title
        filename = f"{title}.{output_format}"  
        output_path = os.path.join(self.config.MERGE_DIR, filename) 

        if os.path.exists(output_path):
            os.remove(output_path)

        command = [self.config.FFMPEG_PATH, '-i', 'concat:' + '|'.join(filepaths), '-acodec', 'copy', output_path]
        subprocess.run(command, check=True)

        merge = Merge(title=title, filepath=output_path, format=output_format)
        data.add_to_merge(merge)
        data.save(data.path)

    def retrieve_merge(self, data : Data):
        merge_list = [m.serialize() for m in data.merge]
        return merge_list
