# StefyTube 

StefyTube è un'applicazione desktop per scaricare, organizzare e riprodurre audio/video da YouTube, con supporto a playlist, interfaccia desktop (via WebView) e gestione locale dei file.

## Features principali

- Possibilità di scaricare video da YouTube in formato mp3 o mp4 (da specificare al momento del download)
- Possibilità di organizzarli in playlist con supporto alla riproduzione casuale (al momento solo per le tracce audio)
- Possibilità di scaricare tutti gli elementi sia audio che video di una playlist

## Miglioramenti futuri

- Possibilità di unire gli elementi di una playlist YT a download concluso
- Miglioramenti generali alla riproduzione video che al momento è stata la sezione che ha ricevuto meno attenzioni
- Pulizia e organizzazione migliore del codice

## Requisiti

[Python 3.11.7](https://www.python.org/downloads/release/python-3117/) (**obbligatorio**)

## Installazione Python

1. Scaricare file adatto (es. Windows installer 64-bit)
2. Avviare il file scaricato
3. Spuntare l'opzione "Add Python 3.x to PATH"
4. "Install now"
5. A installazione completa, chiudere cliccando su "close"

## Installazione (opzionale)

I seguenti passaggi sono opzionali nel caso in cui il progetto venga esportato in uno .zip, il requisito software riguardante python rimane necessario.

L'installazione del progetto verrà comunque fatta dal momento che entrambi i file .bat si occupano di installare le dipendenze elencate nel file requirements.txt

1. Scarica e installa [Python 3.11.7](https://www.python.org/downloads/release/python-3117/)

2. Clona o scarica il progetto:

```
git clone https://github.com/emanuelemuzio/StefyTube.git
cd StefyTube
```

3. Installa le dipendenze:  

``` 
pip install -r requirements.txt
```
Assicurati che ffmpeg sia accessibile nel PATH o indicato nella variabile FFMPEG_PATH nel codice.

## Avvio
Per avviare l'app in modalità desktop (con interfaccia):

```
python app.py --window
```

Per avviarla nel browser (senza interfaccia WebView):

```
python app.py
```

In alternativa è possibile avviare il progetto in una delle due modalità tramite uno dei due collegamenti ai file .bat, ovvero:

- StefyTube.lnk per l'avvio in modalità finestra
- StefyTubeWeb.lnk per avviare il webserver Flask

In entrambi i casi l'applicazione verrà lanciata sulla porta 5000, indirizzo 127.0.0.1

## Struttura

app.py: avvio principale dell'app

templates/: interfacce HTML

static/: file JS/CSS/icone

downloads/: file scaricati

track-playlist/ e video-playlist/: playlist utente

metadata.json: metadati delle tracce audio/video

## Note aggiuntive
L'app non richiede connessione internet costante, salvo per i download.

Tutti i file vengono gestiti in locale, senza invio a server esterni.

Supporta download audio (.mp3) e video (.mp4) in qualità ottimizzata.

## Autore

LinkedIn: https://www.linkedin.com/in/emanuelemuzio-ai-datascientist/

Progetto personale sviluppato per uso educativo e organizzativo.