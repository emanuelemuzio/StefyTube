let trackList = [];
let shuffleTrackList = [];
let currentTrackIndex = 0;
let currentShuffleIndex = 0;
let shuffle = false;
let selectedTrackUuid = '';

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

    if (index < 0 || index >= trackList.length) {
        audio.pause();
        return;
    }

    const activeIndex = shuffle ? trackList.indexOf(shuffleTrackList[index]) : index
    const track = shuffle ? shuffleTrackList[index] : trackList[index]
    const filename = track.filename;
    const title = track.title;
    const track_uuid = track.uuid;
    source.src = `/api/downloads/${track_uuid}`;
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
    const audio = document.getElementById('audioPlayer');
    const source = document.getElementById('audioSource');
    const btn = document.getElementById('shuffleBtn');
    shuffle = !shuffle;

    if (shuffle) {
        btn.innerHTML = '🔀 Riproduzione casuale <span class="badge bg-success ms-2">ATTIVA</span>';
        if (source.src.includes('mp3')) {
            audio.play();
        }
        else {
            document.getElementById('controlsRow').style.display = 'flex';
            playTrack(currentShuffleIndex);
        }
    } else {
        btn.innerHTML = '🔀 Riproduzione casuale';
        audio.pause();
    }

}

function deleteFile(uuid, index) {
    if (!confirm(`Sei sicuro di voler rimuovere la traccia?`)) return;

    fetch('/api/track-player', {
        method: 'DELETE',
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

function fetchProgress() {
    fetch('/api/progress')
        .then(res => res.json())
        .then(progressList => {
            const container = document.getElementById('liveProgressBlock');
            container.innerHTML = ''; // Svuota tutto prima

            progressList.forEach(p => {
                const alert = document.createElement('div');
                alert.className = 'alert alert-info text-center';
                alert.innerHTML = `Download in corso: <strong>${p.filename}</strong> (${p.progress}%)`;
                container.appendChild(alert);
            });
        });
}

function fetchFiles() {
    fetch('/api/track-player-data')
        .then(res => res.json())
        .then(response => {
            const data = response.data;
            trackList = data.tracks;
            shuffleTrackList = shuffleTracks(trackList)

            console.log(trackList)
            console.log(shuffleTrackList)

            const fileList = document.getElementById('fileList');
            const alertBox = document.getElementById('noFilesAlert');
            fileList.innerHTML = '';

            if (trackList.length === 0) {
                alertBox.classList.remove('d-none');
                return;
            }

            alertBox.classList.add('d-none');

            trackList.forEach((track, index) => {
                uuid = track.uuid
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.id = `item-${index + 1}`;

                li.innerHTML = `
            <span>${track.title}</span>
            <div class="d-flex align-items-center gap-2">
              <button class="btn btn-sm" style="background-color:rgb(40, 112, 37);" onclick="playTrack(${index})"><i class="bi bi-play-fill"></i></button>
              <button class="btn btn-sm" style="background-color: #d71612;" onclick="deleteFile('${uuid}', ${index + 1})"><i class="bi bi-trash-fill"></i></button> 
              <button class="btn btn-sm" style="background-color: #d71612; color:white" onclick="openPlaylistModal('${track.title}','${uuid}')">
                Aggiungi a playlist
                </button> 
            </div>
          `;

                fileList.appendChild(li);
            });
        });
}

// Esegui subito al caricamento
document.addEventListener('DOMContentLoaded', () => {
    fetchProgress();
    fetchFiles(); // nuovo

    // Aggiorna ogni 3 secondi
    setInterval(fetchProgress, 3000);

    const audio = document.getElementById('audioPlayer');
    if (audio) {
        audio.addEventListener('ended', () => {
            nextTrack();
        });
    }
});