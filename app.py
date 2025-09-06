import sys
import threading
import webview
import time
import argparse
from flask import Flask 
from src import Config, Service, Data, Router

config = Config()
data = Data.load(config.DATA_PATH)
data.path = config.DATA_PATH
service = Service(config=config)
app = Flask(
    __name__, 
    template_folder=config.TEMPLATE_DIR,
    static_folder=config.STATIC_DIR
)
router = Router(app=app, service=service, data=data) 

# === Avvio ===
def start_flask():
    app.logger.addHandler(config.file_handler)
    app.logger.addHandler(config.console_handler)
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
                data.save(config.DATA_PATH)
                continue

            # Scarico l'entry (ritorna lista di entry completate)
            completed_entries = service.download_entry(entry)

            # Rimuovo l'entry originale dalla queue
            if entry in data.queue:
                data.queue.remove(entry)

            # Aggiungo tutte le entry completate in history
            for e in completed_entries:
                data.move_to_history(e)

            data.save(config.DATA_PATH)

        time.sleep(2)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', action='store_true', default=True, help='Avvia in modalità finestra (PyWebView)')
    args = parser.parse_args()
    
    # Avvia il server Flask in background
    threading.Thread(target=start_flask, daemon=True).start()
    time.sleep(1)
    threading.Thread(target=check_queue, daemon=True).start()

    if args.window and 1 == 2:
        # Modalità finestra (desktop app)
        screen = webview.screens[0] 
        webview.create_window(config.APP_NAME, config.BASE_URL, width=screen.width, height=screen.height)
        webview.start()
    else:
        print(f"Server attivo su {config.BASE_URL}...")
        try:
            while True:
               time.sleep(1)
        except KeyboardInterrupt:
            print("Chiusura server...")

# Chiudi log
sys.stdout.close()
sys.stderr.close()
    