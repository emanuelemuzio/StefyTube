import os
import sys
import threading
import webview
from flask import Flask, render_template, request, jsonify, send_from_directory
from yt_dlp import YoutubeDL
import json
import subprocess
import platform
import re
import unicodedata
import argparse
import webbrowser
import socket
from datetime import datetime, timedelta

# === Percorsi e directory ===

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
FFMPEG_PATH = os.path.join(BASE_DIR, 'ffmpeg.exe')
PLAYLIST_DIR = os.path.join(BASE_DIR, 'playlist') 

# Crea le cartelle se non esistono
os.makedirs(PLAYLIST_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === Logging su file ===
log_path = 'app.log'
sys.stdout = open(log_path, 'w')
sys.stderr = open(log_path, 'w')

app = Flask(__name__, template_folder=TEMPLATE_DIR)
progress_data = []

def clean_progress_data(timeout_sec=120):
    now = datetime.utcnow()
    progress_data[:] = [
        d for d in progress_data
        if d['status'] != 'downloading' or (now - d.get('last_update', now)) < timedelta(seconds=timeout_sec)
    ]

# === Funzione di download ===
# Funzione principale di download
def download_video(url, format_choice):
    entry = {
        'status': 'starting',
        'progress': 0,
        'filename': '',
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
            ext = 'mp3' if format_choice == 'mp3' else 'mp4'
            filename = f"{safe_title}.{ext}"
            progress_data[entry_index]['filename'] = filename
            progress_data[entry_index]['status'] = 'finished'
            progress_data[entry_index]['progress'] = 100
            progress_data[entry_index]['last_update'] = datetime.utcnow()

    # Costruisci le opzioni yt-dlp
    ydl_opts = {
        'progress_hooks': [hook],
        'ffmpeg_location': FFMPEG_PATH,
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
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
                  
def sanitize_filename(title):
    title = unicodedata.normalize('NFKD', title)
    title = re.sub(r'[\\/*?:"<>|]', '_', title)  # Rimuove i caratteri vietati su Windows
    title = re.sub(r'\s+', ' ', title).strip()  # Spazi multipli → uno solo
    return title[:200]  # Evita nomi troppo lunghi

# === Rotte Flask ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format_choice = request.form['format']
    threading.Thread(target=download_video, args=(url, format_choice)).start()
    return jsonify({'message': 'Download avviato'})

@app.route('/progress')
def progress():
    clean_progress_data(timeout_sec=120)
    return jsonify(progress_data)

@app.route('/logo')
def logo():
    return send_from_directory(TEMPLATE_DIR, 'logo-dark.png')

@app.route('/player')
def player():
    files = []
    for f in os.listdir(DOWNLOAD_DIR):
        if f.endswith('.mp3'):
            full_path = os.path.join(DOWNLOAD_DIR, f)
            if os.path.isfile(full_path) and os.path.getsize(full_path) > 0:
                if not any(d['filename'] == f and d['status'] != 'finished' for d in progress_data):
                    files.append(f)

    playlist_files = [os.path.splitext(f)[0] for f in os.listdir(PLAYLIST_DIR) if f.endswith('.json')]
    return render_template('player.html', files=files, playlists=playlist_files, progress=progress_data)

@app.route('/delete-playlist', methods=['POST'])
def delete_playlist():
    name = request.json.get('name')
    file_path = os.path.join(PLAYLIST_DIR, f"{name}.json")

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        return jsonify({'success': False, 'error': 'Playlist non trovata'})

@app.route('/playlist/remove', methods=['POST'])
def remove_from_playlist():
    data = request.json
    playlist = data.get('playlist')
    track = data.get('track')

    path = os.path.join(PLAYLIST_DIR, f'{playlist}.json')
    if not os.path.exists(path):
        return jsonify({'error': 'Playlist non trovata'}), 404

    with open(path, 'r') as f:
        content = json.load(f)

    if track in content['tracks']:
        content['tracks'].remove(track)
        with open(path, 'w') as f:
            json.dump(content, f)
        return jsonify({'success': True})

    return jsonify({'error': 'Brano non trovato nella playlist'}), 404

@app.route('/delete', methods=['POST'])
def delete_file():
    filename = request.json.get('filename')
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    if not filename.endswith('.mp3'):
        return jsonify({'success': False, 'error': 'Formato non valido'})

    if os.path.exists(filepath):
        try:
            os.remove(filepath)

            # 🔁 Rimuovi il brano da tutte le playlist
            for plist_file in os.listdir(PLAYLIST_DIR):
                if plist_file.endswith('.json'):
                    full_path = os.path.join(PLAYLIST_DIR, plist_file)
                    with open(full_path, 'r') as f:
                        data = json.load(f)
                    if filename in data.get('tracks', []):
                        data['tracks'].remove(filename)
                        with open(full_path, 'w') as f:
                            json.dump(data, f, indent=2)

            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        return jsonify({'success': False, 'error': 'File non trovato'})

@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

@app.route('/playlists')
def playlists():
    playlist_files = [f for f in os.listdir(PLAYLIST_DIR) if f.endswith('.json')]
    playlist_names = [os.path.splitext(f)[0] for f in playlist_files]
    return render_template('playlists.html', playlists=playlist_names)

@app.route('/playlist/<name>')
def show_playlist(name):
    path = os.path.join(PLAYLIST_DIR, f'{name}.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return render_template('playlist_view.html', playlist=data, tracks=data, name=name)
    return f'Playlist \"{name}\" non trovata', 404

@app.route('/playlist/create', methods=['POST'])
def create_playlist():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Nome playlist mancante'}), 400
    path = os.path.join(PLAYLIST_DIR, f'{name}.json')
    if os.path.exists(path):
        return jsonify({'error': 'Playlist esistente'}), 409
    with open(path, 'w') as f:
        json.dump({'name': name, 'tracks': []}, f)
    return jsonify({'success': True})

@app.route('/playlist/add', methods=['POST'])
def add_to_playlist():
    data = request.json
    playlist = data.get('playlist')
    track = data.get('track')
    if not playlist or not track:
        return jsonify({'error': 'Parametri mancanti'}), 400

    path = os.path.join(PLAYLIST_DIR, f'{playlist}.json')
    if not os.path.exists(path):
        return jsonify({'error': 'Playlist non trovata'}), 404

    with open(path, 'r') as f:
        content = json.load(f)

    if track not in content['tracks']:
        content['tracks'].append(track)
        with open(path, 'w') as f:
            json.dump(content, f)

    return jsonify({'success': True})

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

@app.route('/open-downloads')
def open_downloads():
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

import time

# === Avvio ===
def start_flask():
    app.run(host='127.0.0.1', port=5000)
    
def open_in_chrome(url='http://127.0.0.1:5000'):
    try:
        chrome = webbrowser.get(using='chrome')
        # chrome.open(url)
        print("Apertura in Chrome riuscita.")
    except webbrowser.Error:
        print("Chrome non trovato. Apro nel browser predefinito.")
        # webbrowser.open(url)
    
def wait_for_flask(host='127.0.0.1', port=5000, timeout=20):
    print(f"Aspetto che Flask sia disponibile su {host}:{port}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                print("Flask è attivo!")
                return True
        except (ConnectionRefusedError, socket.timeout):
            time.sleep(1)
    print("Timeout: Flask non è partito.")
    return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', action='store_true', help='Avvia in modalità finestra (PyWebView)')
    args = parser.parse_args()
    
    print(1)

    # Avvia il server Flask in background
    threading.Thread(target=start_flask, daemon=True).start()

    if args.window:
        # Modalità finestra (desktop app)
        screen = webview.screens[0]
        w = int(screen.width * 0.8)
        h = int(screen.height * 0.8)
        webview.create_window('StefyTube', 'http://127.0.0.1:5000', width=w, height=h)
        webview.start()
    else:
        # modalità browser
        if wait_for_flask():
            open_in_chrome('http://127.0.0.1:5000')
        else:
            print("Non sono riuscito ad aprire il browser: Flask non è partito.")
        input("Premi INVIO per terminare il server...\n")

    # Chiudi log
    sys.stdout.close()
    sys.stderr.close()