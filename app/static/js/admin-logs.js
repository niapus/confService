let offset = 0;
const limit = 100;
let currentFile = "app.log";

async function loadFiles() {
  try {
    const res = await fetch('/api/log-files', { credentials: 'include' });
    if (!res.ok) throw new Error(`Ошибка ${res.status}`);
    const files = await res.json();

    const select = document.getElementById('fileSelect');
    select.innerHTML = files.map(f => {
      const size = f.size_mb != null ? `${f.size_mb} MB` : '0 MB';
      const firstLog = f.first_log_at ? new Date(f.first_log_at).toLocaleString('ru-RU') : '—';
      const modified = f.modified_at ? new Date(f.modified_at).toLocaleString('ru-RU') : '—';
      return `<option value="${f.name}">${f.name} (${size}, первый лог: ${firstLog}, изменен: ${modified})</option>`;
    }).join('');

    select.onchange = () => {
      currentFile = select.value;
      reloadLogs();
    };
  } catch (e) {
    document.getElementById('logBox').textContent = `Ошибка загрузки списка файлов: ${e.message}`;
  }
}

async function reloadLogs() {
  offset = 0;
  const btn = document.querySelector('.load-more');
  btn.disabled = false;
  btn.textContent = 'Загрузить старые';
  try {
    const res = await fetch(`/api/logs?file=${currentFile}&offset=0&limit=${limit}`, { credentials: 'include' });
    if (!res.ok) throw new Error(`Ошибка ${res.status}`);
    const data = await res.json();
    document.getElementById('logBox').textContent = data.lines.join('\n');
  } catch (e) {
    document.getElementById('logBox').textContent = `Ошибка загрузки логов: ${e.message}`;
  }
}

async function loadMore() {
  offset += limit;
  try {
    const res = await fetch(`/api/logs?file=${currentFile}&offset=${offset}&limit=${limit}`, { credentials: 'include' });
    if (!res.ok) throw new Error(`Ошибка ${res.status}`);
    const data = await res.json();

    const nonEmpty = data.lines.filter(l => l.trim() !== '');
    if (nonEmpty.length === 0) {
      offset -= limit;
      const btn = document.querySelector('.load-more');
      btn.disabled = true;
      btn.textContent = 'Все логи загружены';
      return;
    }

    const box = document.getElementById('logBox');
    box.textContent = data.lines.join('\n') + '\n' + box.textContent;
  } catch (e) {
    alert(`Ошибка загрузки старых логов: ${e.message}`);
    offset -= limit;
  }
}

async function autoUpdate() {
  if (!document.getElementById('autoupdate').checked) return;
  try {
    const res = await fetch(`/api/logs?file=${currentFile}&offset=0&limit=${limit}`, { credentials: 'include' });
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('logBox').textContent = data.lines.join('\n');
  } catch (_) {}
}

async function downloadLogFile() {
  if (!currentFile) {
    alert('Выберите файл для скачивания');
    return;
  }
  window.open(`/api/download-log?file=${encodeURIComponent(currentFile)}`, '_blank');
}

setInterval(autoUpdate, 10000);

loadFiles().then(reloadLogs);
