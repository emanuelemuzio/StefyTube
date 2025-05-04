import os
import sys
import threading
import webview
import json
import subprocess
import platform
import time
import re
import unicodedata
import argparse
import webbrowser
import shutil
from flask import Flask, render_template, request, jsonify, send_from_directory
from yt_dlp import YoutubeDL
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

@app.route('/track-playlist-view')
def track_playlist_view():
    
    """ 
    Rotta di dettaglio di una playlist singola.

    Parameters:
        GET: /trackplaylist-view

    Returns:
        Render del template 'playlist-view.html'
    """
    return render_template('track-playlist-view.html')

@app.route('/video-playlist-view')
def video_playlist_view():
    
    """ 
    Rotta di dettaglio di una playlist singola.

    Parameters:
        GET: /video-playlist-view

    Returns:
        Render del template 'playlist-view.html'
    """
    return render_template('video-playlist-view.html')

@app.route('/video-player')
def video_player():  
    return render_template('video-player.html')

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
            noplaylist: bool

    Response:
        message : str
    """
    
    data = request.get_json()
    url = data.get('url')
    format_choice = data.get('format')
    noplaylist = data.get('noplaylist')
    merge = data.get('merge')
    threading.Thread(target=download_video, args=(url, format_choice, noplaylist, merge)).start()
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
    
    try: 
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
                for item in list(filter(lambda x : x['status'] == 'finished', metadata)):
                    path = os.path.join(DOWNLOAD_DIR, f"{item['uuid']}")
                    if os.path.exists(path):
                        os.rename(
                            path,
                            os.path.join(DOWNLOAD_DIR, f"{item['filename']}")
                        )
    except PermissionError as e:
        print('File is locked')
    
    if len(progress_data) > 0:
        clean_progress_data(timeout_sec=30)
        return jsonify({'message' : 'Progress data checked'}), 200
    else:
        return jsonify({'message' : 'Progress data empty'}), 200
    
@app.route('/api/downloads/<file_id>')
def download_file(file_id):
    
    """ 
    API per il recupero del file fisico.

    Parameters:
        GET: /api/downloads/<filename> 
    """
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        filtered = list(filter(lambda x : 'uuid' in x and x['uuid'] == file_id, metadata))
        
        if not filtered:
            print(f"Download fallito: file_id {file_id} non trovato nel metadata.")
            return jsonify({'message': 'File non trovato'}), 404

        file_metadata = filtered[0]
        filename = file_metadata['filename']
        
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
            if isinstance(metadata, list):
                filtered_metadata = list(
                    filter(
                        lambda x : x['format'] == 'mp3' and os.path.exists(os.path.join(DOWNLOAD_DIR, x['filename'])), 
                        metadata
                    )
                )
                data['tracks'] = filtered_metadata 
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

    metadata = []

    # 1. Carica in modo sicuro il metadata
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception:
            metadata = []

    # 2. Rimuovi la traccia se esiste
    track = list(filter(lambda x : 'uuid' in x and x['uuid'] == uuid, metadata))[0]
    metadata = list(filter(lambda x : 'uuid' in x and x['uuid'] != uuid, metadata))
    if not track:
        return jsonify({'message': 'Traccia non trovata nel metadata'}), 404

    # 3. Salva il metadata aggiornato
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
    except Exception as e:
        return jsonify({'message': f'Errore nel salvataggio del metadata: {str(e)}'}), 500

    # 4. Elimina il file fisico associato
    filepath = os.path.join(DOWNLOAD_DIR, track['filename'])
    
    print("File path is :", filepath)
    
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
            
            response['tracks'] = list(filter(lambda x : 'uuid' in x and x['uuid'] in playlist_['track'], metadata))
                
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

@app.post('/api/video-playlist/add')
def add_to_playlist_video():
    data = request.json
    playlist = data.get('playlist')
    video = data.get('video')
    
    if not playlist or not video:
        return jsonify({'message': 'Parametri mancanti'}), 400

    path = os.path.join(VIDEO_PLAYLIST_DIR, f'{playlist}.json')
    
    if not os.path.exists(path):
        return jsonify({'message': 'Playlist non trovata'}), 404

    with open(path, 'r') as f:
        content = json.load(f)

    if video not in content['video']:
        content['video'].append(video)
        with open(path, 'w') as f:
            json.dump(content, f)

    return jsonify({'message': "Operazione effettuata con successo"}), 200

@app.route('/api/video-player-data')
def video_player_data():
    data = {
        'videos' : [],
        'playlists' : []
    }
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            if isinstance(metadata, list):
                filtered_metadata = list(
                    filter(
                        lambda x : x['format'] == 'mp4' and os.path.exists(os.path.join(DOWNLOAD_DIR, x['filename'])), 
                        metadata
                    )
                )
                data['videos'] = filtered_metadata 
    except Exception:
        print('Unreadable file')
        
    for f in os.listdir(VIDEO_PLAYLIST_DIR):
        if f.endswith('.json'):
            playlist_uuid = os.path.splitext(f)[0]
            playlist_path = os.path.join(VIDEO_PLAYLIST_DIR, f)
            with open(playlist_path, 'r', encoding='utf-8') as plfile:
                playlist_ = json.load(plfile)
                playlist_['uuid'] = playlist_uuid
                data['playlists'].append(playlist_)

    return jsonify({
        'message': 'Dati pagina video player recuperati',  
        'data' : data
    }), 200

# === Avvio ===
def start_flask():
    app.run(host=host, port=port) 

# === Funzioni core e di utility di download ===

def merge_files(input_dir, output_path, format_choice):
    files_txt_path = os.path.join(input_dir, 'files.txt')
    with open(files_txt_path, 'w', encoding='utf-8') as f:
        for filename in sorted(os.listdir(input_dir)):
            if filename.endswith(f".{format_choice}"):
                filepath = os.path.join(input_dir, filename)
                f.write(f"file '{filepath.replace('\\', '/')}'\n")
    
    command = [
        FFMPEG_PATH,
        '-f', 'concat',
        '-safe', '0',
        '-i', files_txt_path,
        '-c', 'copy',
        output_path
    ]
    
    subprocess.run(command, check=True)

def save_metadata(entry):

    # Carica il contenuto del file, o inizializza come dizionario vuoto
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                if not isinstance(metadata, list):
                    metadata = []
        except Exception:
            metadata = []
    else:
        metadata = []
        
    metadata_uuids = list(map(lambda x : x['uuid'], list(filter(lambda x : x['format'] == entry['format'], metadata))))

    # Aggiungi o aggiorna l'entry
    if not entry['uuid'] in metadata_uuids:
        metadata.append({
            'uuid' : entry['uuid'],
            'status': entry['status'],
            'filename': entry['filename'],
            'format': entry['format'],
            'title': entry['title'],
            'last_update': datetime.utcnow().isoformat()
        })
        # Sovrascrivi il file
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        
def update_progress(entry):
    progress_data[-1] = entry 

def download_video(url, format_choice, noplaylist, merge):
    
    entry = {
        'uuid': f"{datetime.utcnow().timestamp()}_{format_choice}",
        'status': 'starting',
        'progress': 0,
        'filename': '',
        'title': '',
        'format': format_choice,
        'last_update': datetime.utcnow()
    }
    
    progress_data.append(entry)
    
    def hook(d):
        if d['status'] != 'finished':
            info = d['info_dict']  
            progress_data[-1]['title'] = info.get('title', 'video')
            
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                progress_data[-1]['progress'] = int(downloaded / total * 100)
            progress_data[-1]['status'] = 'downloading'
            return
        
        if not merge:
        
            info = d['info_dict']
            title = sanitize_filename(info.get('title', 'video'))

            ext = 'mp3' if format_choice == 'mp3' else 'mp4'
            filename = f"{title}.{ext}"
            video_id = f"{info.get('id')}.{ext}"
            if not video_id:
                return
            
            progress_data[-1].update({
                'uuid': video_id,
                'status': 'finished',
                'progress': 100,
                'filename': filename,
                'title': title,
                'format': format_choice,
                'last_update': datetime.utcnow()
            })

            save_metadata(progress_data[-1])
        
    ydl_opts = {
        'retries': 10,
        'fragment_retries': 10,
        'http_chunksize': 10485760,
        'nocheckcertificate': True,
        'progress_hooks': [hook],
        'ffmpeg_location': FFMPEG_PATH, 
        'quiet' : True,
    }

    temp_dir = None
    # yt-dlp options
    if merge:
        temp_dir = os.path.join(DOWNLOAD_DIR, f"temp_{uuid4()}")
        os.makedirs(temp_dir, exist_ok=True)
        ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(playlist_index)03d_%(id)s.%(ext)s')
    else:
        ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, '%(id).100s.%(ext)s')

    # Playlist toggle
    if noplaylist:
        ydl_opts['no-playlist'] = True
    else:
        ydl_opts['yes-playlist'] = True

    # Format handling
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
            
            if merge and temp_dir:
                title = sanitize_filename(progress_data[-1]['title'] or 'playlist')
                ext = 'mp3' if format_choice == 'mp3' else 'mp4'
                final_filename = f"{title}_unito.{ext}"
                final_path = os.path.join(DOWNLOAD_DIR, final_filename)

                # Unisci i file
                merge_files(temp_dir, final_path, format_choice)

                # Aggiorna progress e metadata
                playlist_uuid = f"playlist_{datetime.utcnow().timestamp()}_{format_choice}"
                progress_data[-1].update({
                    'uuid': playlist_uuid,
                    'status': 'finished',
                    'progress': 100,
                    'filename': final_filename,
                    'title': title,
                    'format': format_choice,
                    'last_update': datetime.utcnow()
                })

                save_metadata(progress_data[-1])

                # Pulizia della temp dir
                shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(str(e))
        entry = {
            'uuid': f"error_{datetime.utcnow().timestamp()}",
            'status': 'error',
            'progress': 0,
            'filename': str(e),
            'title': '',
            'format': format_choice,
            'last_update': datetime.utcnow()
        }
        save_metadata(entry)
                        
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
        # modalità browser 
        # webbrowser.open(BASE_URL)
        print("Server attivo. Premi Invio per terminare...")
        input()

# Chiudi log
sys.stdout.close()
sys.stderr.close()
    