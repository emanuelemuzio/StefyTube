import os
import threading
from flask import render_template, request, jsonify, send_from_directory
from flask_swagger import swagger
from .requests import *

class Router:
    def __init__(self, app, service, data): 

        # === Views ===

        @app.route('/')
        def download_view():
            
            """ 
            Rotta principale dell'applicazione, per il download dei media da YT. 
            """
            
            return render_template('download.html')

        @app.route('/music')
        def music_view():
            
            """ 
            Rotta del player musicale. 
            """
            
            return render_template('music.html')

        @app.route('/playlist')
        def playlist_view():
            
            """ 
            Rotta della pagina contenente tutte le playlist sia audio che video.  
            """
            
            return render_template('playlist.html')

        @app.route('/music-playlist')
        def music_playlist_view():
            
            """ 
            Rotta di dettaglio di una playlist singola. 
            """
            return render_template('music-playlist.html')

        @app.route('/video-playlist')
        def video_playlist_view():
            
            """ 
            Rotta di dettaglio di una playlist singola.

            Parameters:
                GET: /video-playlist 

            Returns:
                Render del template 'video-playlist.html'
            """
            return render_template('video-playlist.html')

        @app.route('/video')
        def video_view():  
            return render_template('video.html')

        # === API Generiche ===

        @app.post('/api/download')
        def start_download():
            
            """ 
            API per il lancio di un download. 
            """
            
            download_request = DownloadRequest(**request.get_json()) 
            threading.Thread(target=service.download_video, args=(download_request, data)).start()
            return jsonify({'message': 'Download avviato'}), 200

        @app.get('/api/check_queue')
        def check_queue():
            
            """ 
            API per il controllo dei progressi. 
            """
            
            response = service.retrieve_queue(data)
            return jsonify(response), 200
        
        @app.get('/api/check_history')
        def check_history():
            
            """ 
            API per il controllo dei progressi. 
            """
            
            response = service.retrieve_history(data)
            return jsonify(response), 200
            
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


        @app.get('/api/open-download')
        def open_downloads():
            
            """ 
            API per l'apertura della cartella dei download.
            """
            
            return service.open_downloads()

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
                    
                    response['tracks'] = list(filter(lambda x : 'uuid' in x and x['uuid'] in playlist_['track'] and x['format'] == 'mp3', metadata))
                        
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