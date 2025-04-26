let videos = [];
let playlists = [];
let selectedVideoUuid = '';

function openVideoPlaylistModal(videoTitle, videoUuid) {
    selectedVideoUuid = videoUuid;
    document.getElementById('modalVideoName').textContent = videoTitle;

    fetch('/api/playlist-data')
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById('playlistSelect');
            select.innerHTML = '<option selected disabled>Scegli una playlist...</option>';

            (data['video-playlist'] || []).forEach(pl => {
                const option = document.createElement('option');
                option.value = pl.uuid || pl;
                option.textContent = pl.name || pl;
                select.appendChild(option);
            });

            const modal = new bootstrap.Modal(document.getElementById('playlistModal'));
            modal.show();
        });
}

function loadVideos() {
    fetch('/api/video-player-data')
        .then(res => res.json())
        .then(response => {
            const data = response.data
            videos = data.videos;
            playlists = data.playlists;

            const list = document.getElementById('videoList');
            const label = document.getElementById('currentVideoLabel');
            const video = document.getElementById('mainVideo');
            const source = document.getElementById('mainSource');

            list.innerHTML = '';

            if (videos.length === 0) {
                list.innerHTML = `<li class="list-group-item bg-dark text-white text-center">Nessun video disponibile.</li>`;
                source.src = "";
                video.load();
                video.style.display = 'none';
                label.textContent = '';
                return;
            }

            video.style.display = 'block';

            videos.forEach((videoElement, index) => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center bg-dark text-white';
                li.dataset.filename = videoElement;

                const titleSpan = document.createElement('span');
                titleSpan.textContent = videoElement.title;
                titleSpan.classList.add('video-title');
                titleSpan.style.cursor = 'pointer';
                titleSpan.onclick = () => playVideo(videoElement);

                const button = document.createElement('button');
                button.className = 'btn btn-sm';
                button.style = "background-color: #d71612; color:white"
                button.innerHTML = `<button onclick="openVideoPlaylistModal('${videoElement.title}','${videoElement.uuid}')">Aggiungi a playlist</button>`;

                li.appendChild(titleSpan);
                li.appendChild(button);
                list.appendChild(li);
            });

            playVideo(videos[0]); // avvia il primo video
        });
}

function playVideo(videoElement) {
    const video = document.getElementById('mainVideo');
    const source = document.getElementById('mainSource');
    const video_uuid = videoElement.uuid;
    source.src = `/api/downloads/${video_uuid}`;
    video.load();
    video.play();

    document.getElementById('currentVideoLabel').textContent = videoElement.title;
}

function confirmAddToPlaylist() {
    const select = document.getElementById('playlistSelect');
    const playlistUuid = select.value;

    if (!playlistUuid || !selectedVideoUuid) {
        alert("Seleziona una playlist valida");
        return;
    }

    fetch('/api/video-playlist/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            playlist: playlistUuid,
            video: selectedVideoUuid,
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

function confirmAddToVideoPlaylist() {
    const select = document.getElementById('playlistSelect');
    const playlistUuid = select.value;

    if (!playlistUuid || !selectedVideoUuid) {
        alert("Seleziona una playlist valida");
        return;
    }

    fetch('/api/video-playlist/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            playlist: playlistUuid,
            video: selectedVideoUuid,
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

// Inizializzazione
window.onload = () => {
    loadVideos();
};