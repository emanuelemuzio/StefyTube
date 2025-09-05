import os
import threading
from flask import Flask
from flask import render_template, request, jsonify
from flask_swagger import swagger
from .requests import DownloadRequest, HistoryDeleteRequest, QueueDeleteRequest
from .service import Service
from .data import Data

class Router:
    def __init__(self, app : Flask, service : Service, data : Data): 

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
            
            try:
                download_request = DownloadRequest(**request.get_json()) 
                threading.Thread(target=service.download_video, args=(download_request, data)).start()
                return jsonify({'message': 'Download avviato'}), 200
            except Exception as e:
                return jsonify(str(e)), 500

        @app.get('/api/check_queue')
        def check_queue():

            """ 
            API per il controllo dei progressi. 
            """

            try:
                response = service.retrieve_queue(data)
                return jsonify(response), 200
            except Exception as e:
                return jsonify(str(e)), 500
        
        @app.get('/api/check_history')
        def check_history():

            """ 
            API per il controllo dei progressi. 
            """

            try:
                response = service.retrieve_history(data)
                return jsonify(response), 200
            except Exception as e:
                return jsonify(str(e)), 500

        @app.get('/api/open_download_dir')
        def open_download_dir():
            
            """ 
            API per l'apertura della cartella dei download.
            """

            try:
                service.open_download_dir()
                return jsonify("Cartella dei download aperta con successo"), 200
            except Exception as e:
                return jsonify(str(e)), 500

        @app.post('/api/delete_from_history')
        def delete_from_history():

            """ 
            API per la rimozione di un'entry dalla history.
            """

            try:
                delete_request = HistoryDeleteRequest(**request.get_json())
                service.delete_from_history(data, delete_request)
                return jsonify("Rimozione avvenuta con successo"), 200
            except Exception as e:
                return jsonify(str(e)), 500
            
        @app.post('/api/delete_from_queue')
        def delete_from_queue():

            """ 
            API per la rimozione di un'entry dalla queue.
            """

            try:
                delete_request = QueueDeleteRequest(**request.get_json())
                service.delete_from_queue(data, delete_request)
                return jsonify("Rimozione avvenuta con successo"), 200
            except Exception as e:
                return jsonify(str(e)), 500