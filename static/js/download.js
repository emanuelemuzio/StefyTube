const playlistSelect = document.getElementById('noplaylistSelect')
const urlInput = document.getElementById('linkInput');
const fullOption = playlistSelect.querySelector('option[value="false"]');

// Funzione per inviare la richiesta POST
function deleteFromHistory(uuid) {
    fetch('/api/delete_from_history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uuid })
    })
        .then(res => {
            if (res.ok) {
                // Rimuovi il div dall'interfaccia
                const element = document.getElementById(`entry-${uuid}`);
                if (element) element.remove();
            } else {
                // Leggi eventuale messaggio di errore dal JSON
                res.json()
                    .then(data => alert("Errore: " + (data.error || "Errore generico")))
                    .catch(() => alert("Errore generico dal server"));
            }
        })
        .catch(err => alert("Errore nella richiesta: " + err));
}


// Funzione per inviare la richiesta POST
function deleteFromQueue(uuid) {
    fetch('/api/delete_from_queue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uuid })
    })
        .then(res => {
            if (res.ok) {
                // Rimuovi il div dall'interfaccia
                const element = document.getElementById(`entry-${uuid}`);
                if (element) element.remove();
            } else {
                // Leggi eventuale messaggio di errore dal JSON
                res.json()
                    .then(data => alert("Errore: " + (data.error || "Errore generico")))
                    .catch(() => alert("Errore generico dal server"));
            }
        })
        .catch(err => alert("Errore nella richiesta: " + err));
}


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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, format: formatSelected, noplaylist: playlistSelect.value === 'true' })
    })
        .then(res => {
            if (res.ok) {
                urlInput.value = '';
            } else {
                res.json()
                    .then(data => alert("Errore: " + (data.error || "Errore generico")))
                    .catch(() => alert("Errore generico dal server"));
            }
        })
        .catch(err => {
            alert("Errore nella richiesta: " + err);
            console.error(err);
        });
});

function openDownloads(e) {
    e.preventDefault();
    fetch('/api/open_download_dir')
        .then(res => {
            if (res.ok) {
                alert("Cartella aperta con successo");
            } else {
                res.json()
                    .then(data => alert("Errore: " + (data.error || "Errore generico")))
                    .catch(() => alert("Errore generico dal server"));
            }
        })
        .catch(err => alert("Errore nella richiesta: " + err));
}

function checkQueue() {
    fetch('/api/check_queue')
        .then(res => {
            if (!res.ok) {
                // prova a leggere eventuale messaggio di errore dal JSON
                return res.json()
                    .then(data => { throw new Error(data.error || "Errore generico dal server"); })
                    .catch(() => { throw new Error("Errore generico dal server"); });
            }
            return res.json();
        })
        .then(data => {
            const container = document.getElementById('downloadStatus');
            if (!container) return;

            container.innerHTML = ''; // reset

            if (!data.length) return;

            const title = document.createElement('h5');
            title.className = 'mb-2';
            title.textContent = '⏳ Download in corso:';
            container.appendChild(title);

            data.forEach(entry => {
                const entryDiv = renderQueueEntry(entry);
                container.appendChild(entryDiv);
            });
        })
        .catch(err => {
            console.error('Errore durante il fetch dei progressi:', err);
            alert(err.message);
        });
}

function checkHistory() {
    fetch('/api/check_history')
        .then(res => {
            if (!res.ok) {
                // prova a leggere eventuale messaggio di errore dal JSON
                return res.json()
                    .then(data => { throw new Error(data.error || "Errore generico dal server"); })
                    .catch(() => { throw new Error("Errore generico dal server"); });
            }
            return res.json();
        })
        .then(data => {
            const container = document.getElementById('downloadHistory');
            if (!container) return;

            container.innerHTML = ''; // reset

            if (!data.length) return;

            const title = document.createElement('h5');
            title.className = 'mb-2';
            title.textContent = 'Storico download';
            container.appendChild(title);

            data.forEach(entry => {
                const entryDiv = renderHistoryEntry(entry);
                container.appendChild(entryDiv);
            });
        })
        .catch(err => {
            console.error('Errore durante il fetch dei progressi:', err);
            alert(err.message);
        });
}

// Funzione semplice per escape HTML
function escapeHtml(text) {
    return text.replace(/[&<>"']/g, (match) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[match]));
}

// render entry in queue
function renderQueueEntry(entry) {
    const div = document.createElement('div');
    div.className = 'queue-entry';
    div.id = `entry-${entry.uuid}`;
    div.innerHTML = `
        <strong>${entry.title ?? '(in preparazione...)'}</strong><br>
        <small>Formato: ${entry.format?.toUpperCase() ?? 'N/D'} | Stato: ${entry.status ?? 'N/D'} – ${entry.progress ?? 0}%</small>
        <div class="progress">
            <div class="progress-bar" style="width: ${entry.progress ?? 0}%"></div>
        </div>
    `;
    const btn = document.createElement('a');
    btn.href = "#"; // evita comportamento predefinito
    btn.className = 'btn btn-danger btn-sm';
    btn.textContent = 'Elimina';
    btn.addEventListener('click', (e) => {
        e.preventDefault(); // impedisce lo scroll in alto
        deleteFromQueue(entry.uuid);
    });
    div.appendChild(btn);


    return div;
}

// render entry in history
export function renderHistoryEntry(entry) {
    const div = document.createElement('div');
    div.className = 'history-entry';
    div.id = `entry-${entry.uuid}`;
    div.innerHTML = `
        <strong>${entry.title ?? 'Titolo non disponibile'}</strong><br>
        <small>Formato: ${entry.format?.toUpperCase() ?? 'N/D'} | Stato: ${entry.status ?? 'N/D'}</small>
        <br>
    `;
    const btn = document.createElement('a');
    btn.className = 'btn btn-sm btn-danger';
    btn.textContent = 'Elimina';
    btn.addEventListener('click', () => deleteFromHistory(entry.uuid));
    div.appendChild(btn);

    return div;
}

document.getElementById('openDownloadsBtn').onclick = openDownloads;

setInterval(checkQueue, 500);
setInterval(checkHistory, 1000); 