import os
import sys
import threading
import webview
from flask import Flask, render_template, request, jsonify, send_from_directory
from yt_dlp import YoutubeDL
import json
import subprocess
import platform
import time
import re
import unicodedata
import argparse
import webbrowser
from uuid import uuid4
from datetime import datetime, timedelta

# === Percorsi e directory ===
host = '127.0.0.1'
port = 5000
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
FFMPEG_PATH = os.path.join(BASE_DIR, 'ffmpeg.exe')
TRACK_PLAYLIST_DIR = os.path.join(BASE_DIR, 'track-playlist') 
VIDEO_PLAYLIST_DIR = os.path.join(BASE_DIR, 'video-playlist') 
metadata_path = os.path.join(DOWNLOAD_DIR, 'metadata.json')
BASE_URL = f'http://{host}:{port}'
APP_NAME = 'StefyTube'

# Crea le cartelle se non esistono
os.makedirs(TRACK_PLAYLIST_DIR, exist_ok=True)
os.makedirs(VIDEO_PLAYLIST_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === Logging su file ===
log_path = 'log.log'
sys.stdout = open(log_path, 'w')
sys.stderr = open(log_path, 'w')

app = Flask(__name__, template_folder=TEMPLATE_DIR)
progress_data = []

# === Rotte render template ===
 
@app.route('/')
def index():
    
    """ 
    Rotta principale dell'applicazione, nonché del downloader.

    Parameters:
        GET: / 

    Returns:
        Render del template 'download.html'
    """
    
    return render_template('download.html')

@app.route('/track-player')
def track_player():
    
    """ 
    Rotta del player per la gestione delle singole tracce.

    Parameters:
        GET: /track-player

    Returns:
        Render del template 'track-player.html'
    """
    
    return render_template('track-player.html')

@app.route('/playlist')
def playlist():
    
    """ 
    Rotta della pagina contenente tutte le playlist sia audio che video.

    Parameters:
        GET: /playlist

    Returns:
        Render del template 'playlist.html'
    """
    
    return render_template('playlist.html')

@app.route('/playlist-view')
def playlist_view():
    
    """ 
    Rotta di dettaglio di una playlist singola.

    Parameters:
        GET: /playlist-view

    Returns:
        Render del template 'playlist-view.html'
    """
    
    return render_template('playlist-view.html')

# === API Generiche ===

@app.post('/api/start-download')
def start_download():
    
    """ 
    API per il lancio di un download.

    Parameters:
        POST: /api/start-download
        Body:
            url : str
            format: str [mp3, mp4] 

    Response:
        message : str
    """
    
    data = request.get_json()
    url = data.get('url')
    format_choice = data.get('format')
    threading.Thread(target=download_video, args=(url, format_choice)).start()
    return jsonify({'message': 'Download avviato'}), 200

@app.get('/api/progress')
def progress():
    
    """ 
    API per il controllo dei progressi.

    Parameters:
        GET: /api/progress 

    Esempio Response:
        [
            {
                "filename": "8aff8439-8bef-4e9a-952f-3771981a3524.mp4",
                "format": "mp4",
                "last_update": "Sat, 12 Apr 2025 13:56:51 GMT",
                "progress": 0,
                "status": "starting",
                "title": "",
                "uuid": "8aff8439-8bef-4e9a-952f-3771981a3524"
            }
        ]
    """
    
    filtered = [p for p in progress_data if p['status'] != 'finished']
    return jsonify(filtered)

@app.get('/api/clear')
def clear():
    
    """ 
    API per la pulizia dei progressi/download in memoria.

    Parameters:
        GET: /api/clear 

    Response:
        message : str ["Progress data checked", "Progress data empty"]
    """
    
    if len(progress_data) > 0:
        clean_progress_data(timeout_sec=120)
        return jsonify({'message' : 'Progress data checked'}), 200
    else:
        return jsonify({'message' : 'Progress data empty'}), 200
    
@app.route('/api/downloads/<filename>')
def download_file(filename):
    
    """ 
    API per il recupero del file fisico.

    Parameters:
        GET: /api/downloads/<filename> 
    """
    
    return send_from_directory(DOWNLOAD_DIR, filename)

@app.get('/api/open-downloads')
def open_downloads():
    
    """ 
    API per l'apertura della cartella dei download.

    Parameters:
        GET: /api/open-downloads  
    """
    
    download_path = os.path.join(os.getcwd(), 'downloads')

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

# === API mp3 ===

@app.get('/api/track-player-data')
def track_player_data():
    
    """ 
    API per il recupero dei dati per la pagina track-player.

    Parameters:
        GET: /api/track-player-data 

    Esempio Response:
        
    """
    
    data = {
        'tracks' : [],
        'playlists' : []
    }
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            if isinstance(metadata, dict):
                for uuid in metadata.keys():
                    if metadata[uuid]['format'] == 'mp3':
                        data['tracks'].append(metadata[uuid]) 
            else:
                data['tracks'] = []
    except Exception:
        print('Unreadable file')
        
    for f in os.listdir(TRACK_PLAYLIST_DIR):
        if f.endswith('.json'):
            playlist_uuid = os.path.splitext(f)[0]
            playlist_path = os.path.join(TRACK_PLAYLIST_DIR, f)
            with open(playlist_path, 'r', encoding='utf-8') as plfile:
                playlist_ = json.load(plfile)
                playlist_['uuid'] = playlist_uuid
                data['playlists'].append(playlist_)

    return jsonify({
        'message': 'Dati pagina player recuperati',  
        'data' : data
    }), 200
    
@app.delete('/api/track-player')
def track_delete():
    data = request.get_json()
    uuid = data.get('uuid')

    if not uuid:
        return jsonify({'message': 'UUID mancante'}), 400

    metadata = {}

    # 1. Carica in modo sicuro il metadata
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                if not isinstance(metadata, dict):
                    metadata = {}
        except Exception:
            metadata = {}

    # 2. Rimuovi la traccia se esiste
    track = metadata.pop(uuid, None)
    if not track:
        return jsonify({'message': 'Traccia non trovata nel metadata'}), 404

    # 3. Salva il metadata aggiornato
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
    except Exception as e:
        return jsonify({'message': f'Errore nel salvataggio del metadata: {str(e)}'}), 500

    # 4. Elimina il file fisico associato
    filepath = os.path.join(DOWNLOAD_DIR, track.get('filename', ''))
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            return jsonify({'message': f'Errore durante la rimozione del file: {str(e)}'}), 500

    return jsonify({'message': 'Eliminazione completata'}), 200

# === API playlist ===

@app.route('/api/playlist-data')
def playlist_data():
    
    response = {
        'track-playlist' : [],
        'video-playlist' : []
    }
    
    for filename in os.listdir(TRACK_PLAYLIST_DIR):
        if filename.endswith('.json'):
            path = os.path.join(TRACK_PLAYLIST_DIR, filename)
            with open(path, 'r', encoding='utf-8') as f:
                playlist_ = json.load(f)
                uuid = filename.split('.')[0]
                playlist_['uuid'] = uuid
                response['track-playlist'].append(playlist_)
                
    for filename in os.listdir(VIDEO_PLAYLIST_DIR):
        if filename.endswith('.json'):
            path = os.path.join(VIDEO_PLAYLIST_DIR, filename)
            with open(path, 'r', encoding='utf-8') as f:
                playlist_ = json.load(f)
                uuid = filename.split('.')[0]
                playlist_['uuid'] = uuid
                response['video-playlist'].append(playlist_) 
    
    return jsonify(response), 200
    
@app.delete('/api/playlist')
def delete_from_playlist():
    data = request.get_json()
    uuid = data.get('uuid')
    playlist_type = data.get('type')

    if not uuid or playlist_type not in ('track', 'video'):
        return jsonify({'message': 'UUID o tipo di playlist non validi'}), 400

    # Seleziona il path corretto
    if playlist_type == 'track':
        path = os.path.join(TRACK_PLAYLIST_DIR, f'{uuid}.json')
    elif playlist_type == 'video':
        path = os.path.join(VIDEO_PLAYLIST_DIR, f'{uuid}.json')

    # Prova a cancellare il file
    if os.path.exists(path):
        try:
            os.remove(path)
            return jsonify({'message': f'Playlist eliminata con successo'}), 200
        except Exception as e:
            return jsonify({'message': f'Errore durante l\'eliminazione: {str(e)}'}), 500
    else:
        return jsonify({'message': f'Playlist "{uuid}" non trovata'}), 404
    
@app.put('/api/playlist')
def create_playlist():
    data = request.json
    name = data.get('name')
    playlist_type = data.get('type')
    
    if(not(playlist_type == 'track' or playlist_type == 'video')):
        return jsonify({'message': 'Tipologia playlist errata'}), 400
            
    uuid = str(uuid4())
    if not name:
        return jsonify({'message': 'Nome playlist mancante'}), 400
    path = (
        os.path.join(TRACK_PLAYLIST_DIR, f'{uuid}.json') if playlist_type == 'track'
        else os.path.join(VIDEO_PLAYLIST_DIR, f'{uuid}.json') if playlist_type == 'video'
        else None
    )
    with open(path, 'w') as f:
        json.dump({'name': name, playlist_type: [],}, f)
    return jsonify({'message': "Operazione effettuata con successo"}), 200
    
# === API track playlist

@app.get('/api/track-playlist-data')
def retrieve_playlist_tracks():
    uuid = request.args.get('uuid')
    response = { 
        'tracks' : [],
        'name' : ''
    }
    
    with open(os.path.join(TRACK_PLAYLIST_DIR, f'{uuid}.json'), 'r', encoding='utf-8') as playlistfile:
        playlist_ = json.load(playlistfile)
        response['name'] = playlist_['name']
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
            for track in playlist_['track']:
                response['tracks'].append(metadata[track])
                
            return jsonify(response), 200

@app.post('/api/track-playlist/add')
def add_to_playlist():
    data = request.json
    playlist = data.get('playlist')
    track = data.get('track')
    
    if not playlist or not track:
        return jsonify({'message': 'Parametri mancanti'}), 400

    path = os.path.join(TRACK_PLAYLIST_DIR, f'{playlist}.json')
    
    if not os.path.exists(path):
        return jsonify({'message': 'Playlist non trovata'}), 404

    with open(path, 'r') as f:
        content = json.load(f)

    if track not in content['track']:
        content['track'].append(track)
        with open(path, 'w') as f:
            json.dump(content, f)

    return jsonify({'message': "Operazione effettuata con successo"}), 200

@app.route('/video-player')
def video_player():
    videos = []
    for f in os.listdir(DOWNLOAD_DIR):
        if f.endswith('.mp4'):
            full_path = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(full_path) and os.path.getsize(full_path) > 0:
                # Escludi file ancora in download
                if not any(d['filename'] == f and d['status'] != 'finished' for d in progress_data):
                    videos.append(f)

    return render_template('video_player.html', videos=videos, progress=progress_data)

# === Avvio ===
def start_flask():
    app.run(host=host, port=port) 

# === Funzioni core e di utility di download ===

def save_metadata(entry):

    # Carica il contenuto del file, o inizializza come dizionario vuoto
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                if not isinstance(metadata, dict):
                    metadata = {}
        except Exception:
            metadata = {}
    else:
        metadata = {}

    # Aggiungi o aggiorna l'entry
    metadata[str(entry['uuid'])] = {
        'status': entry['status'],
        'filename': entry['filename'],
        'format': entry['format'],
        'title': entry['title'],
        'last_update': datetime.utcnow().isoformat()
    }

    # Sovrascrivi il file
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

def download_video(url, format_choice):
    uuid = str(uuid4())
    
    entry = {
        'status': 'starting',
        'progress': 0,
        'filename': f'{uuid}.{format_choice}',
        'title' : '',
        'uuid' : uuid,
        'format': format_choice,
        'last_update': datetime.utcnow()
    }

    progress_data.append(entry)
    entry_index = len(progress_data) - 1  # usato per aggiornare questo specifico download

    def hook(d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total_bytes:
                percent = int(downloaded / total_bytes * 100)
                progress_data[entry_index]['progress'] = percent
                progress_data[entry_index]['status'] = 'downloading'
                progress_data[entry_index]['last_update'] = datetime.utcnow()

        elif d['status'] == 'finished':
            raw_title = d['info_dict'].get('title', 'video')
            safe_title = sanitize_filename(raw_title)
            # ext = 'mp3' if format_choice == 'mp3' else 'mp4'
            # filename = f"{safe_title}.{ext}"
            # progress_data[entry_index]['filename'] = filename
            progress_data[entry_index]['status'] = 'finished'
            progress_data[entry_index]['progress'] = 100
            progress_data[entry_index]['title'] = safe_title
            progress_data[entry_index]['last_update'] = datetime.utcnow()

    # Costruisci le opzioni yt-dlp
    ydl_opts = {
        'progress_hooks': [hook],
        'ffmpeg_location': FFMPEG_PATH,
        'outtmpl': os.path.join(DOWNLOAD_DIR, f'{uuid}.%(ext)s'),
        'quiet': True,
    }

    if format_choice == 'mp3':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif format_choice == 'mp4':
        ydl_opts['format'] = 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/mp4'
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        progress_data[entry_index]['status'] = 'error'
        progress_data[entry_index]['progress'] = 0
        progress_data[entry_index]['filename'] = str(e)
        progress_data[entry_index]['last_update'] = datetime.utcnow()
    finally:
        save_metadata(progress_data[entry_index])
                  
def sanitize_filename(title):
    title = unicodedata.normalize('NFKD', title)
    title = re.sub(r'[\\/*?:"<>|]', '_', title)  # Rimuove i caratteri vietati su Windows
    title = re.sub(r'\s+', ' ', title).strip()  # Spazi multipli → uno solo
    return title[:200]  # Evita nomi troppo lunghi

def clean_progress_data(timeout_sec=20):
    now = datetime.utcnow()
    progress_data[:] = [
        d for d in progress_data
        if d['status'] != 'downloading' or (now - d.get('last_update', now)) < timedelta(seconds=timeout_sec)
    ]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', action='store_true', help='Avvia in modalità finestra (PyWebView)')
    args = parser.parse_args()
    
    # Avvia il server Flask in background
    threading.Thread(target=start_flask, daemon=True).start()
    time.sleep(1)

    if args.window == True:
        # Modalità finestra (desktop app)
        screen = webview.screens[0] 
        webview.create_window(APP_NAME, BASE_URL, width=screen.width, height=screen.height)
        webview.start()
    else:
    #     # modalità browser 
        # webbrowser.open(BASE_URL)
        print("Server attivo. Premi Invio per terminare...")
        input()


# Chiudi log
sys.stdout.close()
sys.stderr.close()
    