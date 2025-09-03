let lastStartedDownload = null;
const playlistSelect = document.getElementById('noplaylistSelect')
const urlInput = document.getElementById('linkInput');

playlistSelect.addEventListener('change', () => {
    const url = urlInput.value;
    const isPlaylist = url.includes('list=');
});

urlInput.addEventListener('input', () => {
    const url = urlInput.value;
    const fullOption = playlistSelect.querySelector('option[value="false"]');
    const isPlaylist = url.includes('list=');

    // Abilita/disabilita opzione "scarica playlist"
    fullOption.disabled = !isPlaylist;

    // Se l'opzione è disabilitata ed è selezionata, forza il valore su "true"
    if (!isPlaylist && playlistSelect.value === 'true') {
        playlistSelect.value = 'true';
    }
});


$('#downloadForm').on('submit', function (e) {
    e.preventDefault();

    const formatSelected = $('#formatSelect').val();
    const url = $('input[name="url"]').val();

    $('#statusMessage').text('');

    fetch('/api/start-download', {
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
            lastStartedDownload = { format: formatSelected };  // usa per filtrare i progressi
            urlInput.value = ''
        });
});

function openDownloads(e) {
    e.preventDefault();
    fetch('/open-downloads')
        .then(res => res.json())
        .then(data => {
            if (!data.success) alert("Errore: " + data.error);
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

            container.innerHTML = '<h5 class="mb-2">⏳ Download in corso:</h5>' + data.map(d =>
                `<div class="mb-2 p-2 bg-dark text-light rounded">
            <strong>${d.title || '(in preparazione...)'}</strong><br>
            Formato: ${d.format?.toUpperCase() || 'N/D'}<br>
            Stato: ${d.status} – ${d.progress}%
            <div class="progress mt-1" style="height: 8px;">
              <div class="progress-bar" style="background-color: #d71612; width: ${d.progress}%"></div>
            </div>
          </div>`
            ).join('');
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

            container.innerHTML = '<h5 class="mb-2">Storico download:</h5>' + data.map(d =>
                `<div class="mb-2 p-2 bg-dark text-light rounded">
            <strong>${d.title || 'Non disponibile'}</strong><br>
            Formato: ${d.format?.toUpperCase() || 'N/D'}<br>
            <a href="${d.url || '#'}">Link</a><br>
            Stato: ${d.status}
            <div class="progress mt-1" style="height: 8px;">
              <div class="progress-bar" style="background-color: #d71612; width: ${d.progress}%"></div>
            </div>
          </div>`
            ).join('');
        })
        .catch(err => {
            console.error('Errore durante il fetch dei progressi:', err);
        });
}

checkQueue()
checkHistory()

setInterval(checkQueue, 1000); 
setInterval(checkHistory, 1000); 