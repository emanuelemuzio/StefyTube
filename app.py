import os
import sys
import threading
import webview
from flask import Flask, render_template, request, jsonify, send_from_directory
from yt_dlp import YoutubeDL
import json
import subprocess
import platform

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
progress_data = {'status': 'idle', 'progress': 0, 'filename': ''}

# === Funzione di download ===
def download_video(url, format_choice):
    def hook(d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                progress_data['progress'] = int(downloaded_bytes / total_bytes * 100)
                progress_data['status'] = 'downloading'
        elif d['status'] == 'finished':
            progress_data['progress'] = 100
            progress_data['status'] = 'finished'
            progress_data['filename'] = d['info_dict'].get('title', '')

    ydl_opts = {
        'ffmpeg_location': FFMPEG_PATH,
        'progress_hooks': [hook],
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4'
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

    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except Exception as e:
            progress_data['status'] = 'error'
            progress_data['progress'] = 0
            progress_data['filename'] = str(e)

# === Rotte Flask ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format_choice = request.form['format']
    progress_data['status'] = 'starting'
    progress_data['progress'] = 0
    progress_data['filename'] = ''
    threading.Thread(target=download_video, args=(url, format_choice)).start()
    return jsonify({'message': 'Download avviato'})

@app.route('/progress')
def progress():
    return jsonify(progress_data)

@app.route('/logo')
def logo():
    return send_from_directory(TEMPLATE_DIR, 'logo-dark.png')

@app.route('/player')
def player():
    files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.mp3')]
    playlist_files = [os.path.splitext(f)[0] for f in os.listdir(PLAYLIST_DIR) if f.endswith('.json')]
    return render_template('player.html', files=files, playlists=playlist_files)

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
        with open(path, 'r') as f:
            data = json.load(f)
            return render_template('playlist_view.html', playlist=data)
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
    videos = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.mp4')]
    return render_template('video_player.html', videos=videos)

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

# === Avvio ===
def start_flask():
    app.run()

if __name__ == '__main__':
    threading.Thread(target=start_flask, daemon=True).start()
    screen = webview.screens[0]
    w = screen.width
    h = screen.height
    webview.create_window(
        'StefyTube',
        'http://127.0.0.1:5000',
        width=w,
        height=h
    )
    webview.start()

    # Chiudi log
    sys.stdout.close()
    sys.stderr.close()