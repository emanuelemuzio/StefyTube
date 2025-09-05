import { renderQueueEntry, renderHistoryEntry } from "./render.js"; { }
const playlistSelect = document.getElementById('noplaylistSelect')
const urlInput = document.getElementById('linkInput');
const fullOption = playlistSelect.querySelector('option[value="false"]');

urlInput.addEventListener('input', () => {
    const url = urlInput.value;
    const isPlaylist = url.includes('list=');

    // Abilita/disabilita opzione "scarica playlist"
    fullOption.disabled = !isPlaylist;

    // Se l'opzione è disabilitata ed era selezionata, forza un valore valido
    if (!isPlaylist && playlistSelect.value === 'false') {
        playlistSelect.value = 'true'; // o "true" a seconda della logica
    }
});

$('#downloadForm').on('submit', function (e) {
    e.preventDefault();

    const formatSelected = $('#formatSelect').val();
    const url = $('input[name="url"]').val();

    $('#statusMessage').text('');

    fetch('/api/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            url: url,
            format: formatSelected,
            noplaylist: playlistSelect.value === 'true'
        })
    })
        .then(() => {
            urlInput.value = ''
        });
});

function openDownloads(e) {
    e.preventDefault();
    fetch('/api/open-download')
        .then(res => res.json())
        .then(data => {
            if (!data.success) alert("Errore: " + data.error);
            alert("Cartella aperta con successo")
        });
}

function checkQueue() {
    fetch('/api/check_queue')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('downloadStatus');

            if (!container) return;

            if (!data.length) {
                container.innerHTML = '';
                return;
            }

            container.innerHTML = '<h5 class="mb-2">⏳ Download in corso:</h5>' + data.map(renderQueueEntry).join('');

        })
        .catch(err => {
            console.error('Errore durante il fetch dei progressi:', err);
        });
}

function checkHistory() {
    fetch('/api/check_history')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('downloadHistory');

            if (!container) return;

            if (!data.length) {
                container.innerHTML = '';
                return;
            }

            container.innerHTML = '<h5 class="mb-2">Storico download:</h5>' + data.map(renderHistoryEntry).join('');
        })
        .catch(err => {
            console.error('Errore durante il fetch dei progressi:', err);
        });
}

document.getElementById('openDownloadsBtn').onclick = openDownloads;

setInterval(checkQueue, 500);
setInterval(checkHistory, 1000); 