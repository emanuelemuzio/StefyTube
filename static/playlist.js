document.getElementById('createForm').addEventListener('submit', async function (e) {
  e.preventDefault();
  const name = document.getElementById('playlistName').value.trim();
  const type = document.getElementById('playlistType').value;
  const res = await fetch('/api/playlist', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, type })
  });
  const data = await res.json();
  if (res.status == 200) {
    fetchPlaylists();  
    location.reload();
  } else {
    alert(data.message);
  }
});

function deletePlaylist(uuid, type) {
  if (!confirm(`Sei sicuro di voler eliminare la playlist?`)) return;

  fetch('/api/playlist', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uuid, type })
  })
    .then(res => res.json())
    .then(data => {
      alert(data.message);
      fetchPlaylists();   
    });
}


function fetchPlaylists() {
  fetch('/api/playlist-data')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById('playlistList');
      container.innerHTML = '';

      const renderGroup = (playlists, typeLabel, typeValue) => {
        if (playlists.length > 0) {
          const header = document.createElement('li');
          header.className = 'list-group-item text-center fw-bold bg-secondary text-white';
          header.textContent = typeLabel;
          container.appendChild(header);
        }

        playlists.forEach(playlist => {
          const li = document.createElement('li');
          li.className = 'list-group-item bg-dark text-white d-flex justify-content-between align-items-center';

          li.innerHTML = `
              <a href="/${typeValue}-playlist-view?id=${playlist.uuid}" class="btn btn-sm px-4" style="background-color: #d71612; color:white">
                ${playlist.name}
              </a>
              <div class="d-flex gap-2">
                <button class="btn btn-sm" style="background-color: #d71612;" onclick="deletePlaylist('${playlist.uuid}', '${typeValue}')"><i class="bi bi-trash-fill"></i></button>
              </div>
            `;

          container.appendChild(li);
        });
      };

      renderGroup(data['track-playlist'], 'Musica', 'track');
      renderGroup(data['video-playlist'], 'Video', 'video');
    });
}


document.addEventListener('DOMContentLoaded', () => {
  fetchPlaylists();
});