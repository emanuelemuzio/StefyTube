let trackList = [];
let shuffleTrackList = [];
let currentTrackIndex = 0;
let currentShuffleIndex = 0;
let shuffle = false;
let selectedTrackUuid = '';
let selectedTracks = [];

// Aggiungo un elemento alla lista temporanea
function addToMergeList(title, uuid) {
    if (selectedTracks.includes(uuid)) return;

    selectedTracks.push(uuid);

    const container = document.getElementById("mergeContainer");
    container.style.display = "block"; // mostra container

    const ul = document.getElementById("mergeList");
    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";
    li.id = `merge-${uuid}`;
    li.innerHTML = `
        <span>${title}</span>
        <button class="btn btn-sm btn-danger" onclick="removeFromMergeList('${uuid}')">Rimuovi</button>
    `;
    ul.appendChild(li);
}

// Rimuovo un elemento dalla lista temporanea
function removeFromMergeList(uuid) {
    selectedTracks = selectedTracks.filter(id => id !== uuid);
    const li = document.getElementById(`merge-${uuid}`);
    if (li) li.remove();

    if (!selectedTracks.length) {
        document.getElementById("mergeContainer").style.display = "none"; // nascondi se vuoto
    }
}

// Invio al backend
function sendMergeRequest() {
    if (!selectedTracks.length) {
        alert("Nessuna traccia selezionata");
        return;
    }

    const mergeName = document.getElementById("mergeName").value.trim();
    if (!mergeName) {
        alert("Inserisci un nome per il file merge");
        return;
    }

    fetch("/api/merge_uuid_list", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uuids: selectedTracks, title: mergeName })
    })
        .then(res => {
            if (res.ok) {
                alert("Merge avviato con successo");
                selectedTracks = [];
                document.getElementById("mergeList").innerHTML = "";
                document.getElementById("mergeContainer").style.display = "none";
                document.getElementById("mergeName").value = "";
                fetchFiles()
            } else {
                return res.json()
                    .then(data => alert("Errore: " + (data.error || "Errore generico")))
                    .catch(() => alert("Errore generico dal server"));
            }
        })
        .catch(err => alert("Errore nella richiesta: " + err));
}

function openPlaylistModal(trackTitle, trackUuid) {
    selectedTrackUuid = trackUuid;
    document.getElementById('modalTrackName').textContent = trackTitle;

    // Carica playlist di tipo "track"
    fetch('/api/playlist-data')
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById('playlistSelect');
            select.innerHTML = '<option selected disabled>Scegli una playlist...</option>';

            (data['track-playlist'] || []).forEach(pl => {
                const option = document.createElement('option');
                option.value = pl.uuid || pl;  // supporta sia {uuid, name} che stringa
                option.textContent = pl.name || pl;
                select.appendChild(option);
            });

            const modal = new bootstrap.Modal(document.getElementById('playlistModal'));
            modal.show();
        });
}

function confirmAddToPlaylist() {
    const select = document.getElementById('playlistSelect');
    const playlistUuid = select.value;

    if (!playlistUuid || !selectedTrackUuid) {
        alert("Seleziona una playlist valida");
        return;
    }

    fetch('/api/track-playlist/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            playlist: playlistUuid,
            track: selectedTrackUuid,
        })
    })
        .then(res => res.json())
        .then(data => {
            alert(data.message || 'Aggiunta completata');
            bootstrap.Modal.getInstance(document.getElementById('playlistModal')).hide();
        })
        .catch(err => {
            console.error(err);
            alert("Errore durante l’aggiunta alla playlist");
        });
}

function shuffleTracks(originalArray) {
    const array = [...originalArray]; // crea una copia
    let currentIndex = array.length;

    while (currentIndex !== 0) {
        const randomIndex = Math.floor(Math.random() * currentIndex);
        currentIndex--;

        // Scambia gli elementi
        [array[currentIndex], array[randomIndex]] = [
            array[randomIndex], array[currentIndex]
        ];
    }

    return array;
}


function playTrack(index) {

    currentTrackIndex = index;
    currentShuffleIndex = index;

    const audio = document.getElementById('audioPlayer');
    const source = document.getElementById('audioSource');
    const nowPlaying = document.getElementById('nowPlaying');

    if (index < 0 || index >= trackList.length || index >= shuffleTrackList.length) {
        index = 0;
        currentTrackIndex = 0;
        currentShuffleIndex = 0;
    }

    const activeIndex = shuffle ? trackList.indexOf(shuffleTrackList[index]) : index
    const track = shuffle ? shuffleTrackList[index] : trackList[index]
    const title = track.title;
    const track_uuid = track.uuid;
    source.src = `/api/play/${track_uuid}`;
    audio.load();
    audio.play();

    document.querySelectorAll('.track-active').forEach(el => {
        el.classList.remove('track-active');
    });

    // Aggiungi highlight a quello in riproduzione
    const activeItem = document.getElementById(`item-${activeIndex + 1}`);
    if (activeItem) {
        activeItem.classList.add('track-active');
    }

    audio.hidden = false;
    nowPlaying.textContent = `In riproduzione: ${title}`;
}

function nextTrack() {
    if (shuffle) {
        currentShuffleIndex++;
        playTrack(currentShuffleIndex);
    } else {
        currentTrackIndex++;
        playTrack(currentTrackIndex);
    }
}

function prevTrack() {
    if (shuffle) {
        currentShuffleIndex--;
        playTrack(currentShuffleIndex);
    } else {
        currentTrackIndex--;
        playTrack(currentTrackIndex);
    }
}

function toggleShuffle() {
    const btn = document.getElementById('shuffleBtn');
    shuffle = !shuffle;

    if (shuffle) {
        btn.innerHTML = '🔀 Riproduzione casuale <span class="badge bg-success ms-2">ATTIVA</span>';
        document.getElementById('controlsRow').style.display = 'flex';
    } else {
        btn.innerHTML = '🔀 Riproduzione casuale';
    }
}

function deleteFile(uuid, index) {
    if (!confirm(`Sei sicuro di voler rimuovere la traccia?`)) return;

    fetch('/api/delete_from_history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 'uuid': uuid })
    })
        .then(res => res.json())
        .then(_ => {
            document.getElementById(`item-${index}`).remove();
            nowPlaying.textContent = '';
            audio.pause();
        });

}

function deleteMerge(uuid, index) {
    if (!confirm("Sei sicuro di voler rimuovere la traccia?")) return;

    fetch('/api/delete_from_merge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uuid })
    })
        .then(res => {
            if (!res.ok) throw new Error("Errore dal server");
            return res.json();
        })
        .then(data => {
            const li = document.getElementById(`item-${index}`);
            if (li) li.remove();

            const nowPlaying = document.getElementById('nowPlaying');
            const audio = document.getElementById('audioPlayer');
            if (nowPlaying) nowPlaying.textContent = '';
            if (audio) audio.pause();
            fetchFiles()
        })
        .catch(err => alert("Errore nella richiesta: " + err));
}


function addToPlaylist(track, playlist) {
    fetch('/api/playlist/add-track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playlist, track })
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert(`Aggiunto a "${playlist}"`);
            } else {
                alert('Errore: ' + data.error);
            }
        });
}

function fetchFiles() {
    const fileList = document.getElementById('fileList');
    const alertBox = document.getElementById('noFilesAlert');

    // Reset lista
    trackList = [];
    fileList.innerHTML = '';

    // Fetch tracce normali
    fetch('/api/check_history')
        .then(res => res.json())
        .then(response => {
            trackList = response || [];

            // Fetch merge files e unirli
            return fetch('/api/check_merge')
                .then(res => res.json())
                .then(mergeFiles => {
                    if (mergeFiles && mergeFiles.length) {
                        // Considera anche i merge come tracce normali
                        mergeFiles.forEach(merge => {
                            trackList.push({
                                uuid: merge.uuid,
                                title: merge.title ?? 'Merge file',
                                filepath: merge.filepath,
                                format: merge.format ?? 'mp3',
                                isMerge: true // flag opzionale se vuoi distinguere
                            });
                        });
                    }

                    // Shuffle e render
                    shuffleTrackList = shuffleTracks(trackList);

                    if (!trackList.length) {
                        alertBox.classList.remove('d-none');
                        return;
                    } else {
                        alertBox.classList.add('d-none');
                    }

                    // Render lista
                    trackList.forEach((track, index) => {
                        const uuid = track.uuid;
                        const li = document.createElement('li');
                        li.className = 'list-group-item d-flex justify-content-between align-items-center';
                        if (track.isMerge) {
                            li.classList.add('merge-entry');
                        }
                        li.id = `item-${index + 1}`;

                        li.innerHTML = `
                        <span>${track.title} ${track.isMerge ? '<span class="badge bg-danger ms-2">MERGE</span>' : ''}</span>
                        <div class="d-flex align-items-center gap-2">
                            <button class="btn btn-sm" style="background-color:rgb(40, 112, 37);" onclick="playTrack(${index})">
                                <i class="bi bi-play-fill"></i>
                            </button>
                            <button class="btn btn-sm" style="background-color: #d71612;" 
                                onclick="${track.isMerge ? `deleteMerge('${uuid}')` : `deleteFile('${uuid}', ${index + 1})`}">
                                <i class="bi bi-trash-fill"></i>
                            </button>
                            <button class="btn btn-sm btn-secondary" onclick="addToMergeList('${track.title}', '${uuid}')">
                                Aggiungi a lista merge
                            </button>
                        </div>
                    `;
                        fileList.appendChild(li);
                    });
                });
        })
        .catch(err => console.error('Errore nel fetch dei file:', err));
}

// Esegui subito al caricamento
document.addEventListener('DOMContentLoaded', () => {
    fetchFiles(); // nuovo 

    const audio = document.getElementById('audioPlayer');
    if (audio) {
        audio.addEventListener('ended', () => {
            nextTrack();
        });
    }
});

function openMerge(e) {
    e.preventDefault();
    fetch('/api/open_merge_dir')
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

document.getElementById('openMergeBtn').onclick = openMerge;