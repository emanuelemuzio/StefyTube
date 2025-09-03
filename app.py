import sys
import threading
import webview
import time
import argparse
from flask import Flask 
from src import Config, Service, Data, Router

config = Config()
data = Data.load(config.DATA_PATH)
service = Service(config=config)
app = Flask(__name__, template_folder=config.TEMPLATE_DIR)
router = Router(app=app, service=service, data=data)

# Dependency tree: 
# router
#   <- app
#       <- config
#   <- service
#       <- data
#           <- config
#       <- config

# === Avvio ===
def start_flask():
    app.run(host=config.host, port=config.port)

def check_queue():
    while True:
        for entry in list(data.queue):
            # Entry duplicata o già completata
            if not data.should_download(entry):
                print(f"Video duplicato: {entry.title or entry.url} (ID: {entry.id})")
                entry.status = "duplicate"
                data.queue.remove(entry)
                data.move_to_history(entry)
                data.save()
                continue

            # Scarico l'entry (ritorna lista di entry completate)
            completed_entries = service.download_entry(entry)

            # Rimuovo l'entry originale dalla queue
            if entry in data.queue:
                data.queue.remove(entry)

            # Aggiungo tutte le entry completate in history
            for e in completed_entries:
                data.move_to_history(e)

            data.save()

        time.sleep(2)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', action='store_true', help='Avvia in modalità finestra (PyWebView)')
    args = parser.parse_args()
    
    # Avvia il server Flask in background
    threading.Thread(target=start_flask, daemon=True).start()
    time.sleep(1)
    threading.Thread(target=check_queue, daemon=True).start()

    if args.window == True:
        # Modalità finestra (desktop app)
        screen = webview.screens[0] 
        webview.create_window(config.APP_NAME, config.BASE_URL, width=screen.width, height=screen.height)
        webview.start()
    else:
        # modalità browser 
        # webbrowser.open(BASE_URL)
        print("Server attivo...")
        input()

# Chiudi log
sys.stdout.close()
sys.stderr.close()
    