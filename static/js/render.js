export function renderQueueEntry(entry) {
    const progress = entry.progress ?? 0;
    const title = entry.title ? escapeHtml(entry.title) : '(in preparazione...)';
    const format = entry.format?.toUpperCase() ?? 'N/D';
    const status = escapeHtml(entry.status ?? 'N/D');

    return `
    <div class="mb-2 p-2 bg-dark text-light rounded">
        <strong>${title}</strong><br>
        Formato: ${format}<br>
        Stato: ${status} – ${progress}%
        <div class="progress mt-1" style="height: 8px;">
            <div class="progress-bar" style="background-color: #d71612; width: ${progress}%"></div>
        </div>
    </div>
    `;
}

// Funzione semplice per escape HTML
export function escapeHtml(text) {
    return text.replace(/[&<>"']/g, (match) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[match]));
}

export function renderHistoryEntry(entry) {
    const progress = entry.progress ?? 0;
    const title = entry.title ? escapeHtml(entry.title) : 'Titolo non disponibile';
    const format = entry.format?.toUpperCase() ?? 'N/D';
    const status = escapeHtml(entry.status ?? 'N/D');

    return `
    <div class="mb-2 p-2 bg-dark text-light rounded">
        <strong>${title}</strong><br>
        Formato: ${format}<br>
        Stato: ${status} 
    </div>
    `;
}