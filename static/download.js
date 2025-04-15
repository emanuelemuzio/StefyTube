let lastStartedDownload = null;
const playlistSelect = document.getElementById('noplaylistSelect')
const urlInput = document.getElementById('linkInput');

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

function updateDownloadStatus() {
    fetch('/api/progress')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('downloadStatus');
            if (!container) return;

            // Filtra solo download non completati
            const active = data.filter(d => d.status !== 'finished' && d.progress < 100);

            if (!active.length) {
                container.innerHTML = '';
                return;
            }

            container.innerHTML = '<h5 class="mb-2">⏳ Download in corso:</h5>' + active.map(d =>
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


setInterval(updateDownloadStatus, 500);
// updateDownloadStatus();