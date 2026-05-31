/**
 * DocAI — Frontend Application
 * Handles file upload, question submission, and long-polling for answers.
 */

/* ────────────────────────────────────────────
   Constants & State
──────────────────────────────────────────── */
const API = {
  UPLOAD:  '/api/upload',
  ASK:     '/api/ask',
  ANSWER:  '/api/answer',
};

const POLL_INTERVAL_MS = 1500;
const POLL_MAX_RETRIES = 40;

let state = {
  sessionId:  null,
  file:       null,
  isUploading: false,
  isAsking:    false,
};

/* ────────────────────────────────────────────
   DOM References
──────────────────────────────────────────── */
const $ = id => document.getElementById(id);

const el = {
  dropZone:      $('dropZone'),
  fileInput:     $('fileInput'),
  browseBtn:     $('browseBtn'),
  fileInfo:      $('fileInfo'),
  fileName:      $('fileName'),
  fileSize:      $('fileSize'),
  removeFile:    $('removeFile'),
  uploadBtn:     $('uploadBtn'),
  sessionBadge:  $('sessionBadge'),
  sessionId:     $('sessionId'),
  chatPanel:     $('chatPanel'),
  chatWindow:    $('chatWindow'),
  chatEmpty:     $('chatEmpty'),
  questionInput: $('questionInput'),
  sendBtn:       $('sendBtn'),
  statusPill:    $('statusPill'),
  statusText:    $('statusPill').querySelector('.status-text'),
  toastContainer:$('toastContainer'),
};

/* ────────────────────────────────────────────
   Status Pill
──────────────────────────────────────────── */
function setStatus(text, type = '') {
  el.statusPill.className = `header-pill ${type}`;
  el.statusText.textContent = text;
}

/* ────────────────────────────────────────────
   Toast Notifications
──────────────────────────────────────────── */
function showToast(message, type = 'info', duration = 4000) {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  el.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'toastOut 0.3s ease forwards';
    toast.addEventListener('animationend', () => toast.remove());
  }, duration);
}

/* ────────────────────────────────────────────
   File Handling
──────────────────────────────────────────── */
function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function applyFile(file) {
  const allowed = ['.pdf', '.docx', '.txt', '.md'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast(`Unsupported file type: ${ext}`, 'error');
    return;
  }
  const maxBytes = 10 * 1024 * 1024;
  if (file.size > maxBytes) {
    showToast('File exceeds 10 MB limit.', 'error');
    return;
  }

  state.file = file;
  el.fileName.textContent = file.name;
  el.fileSize.textContent = formatBytes(file.size);
  el.fileInfo.hidden = false;
  el.dropZone.hidden = true;
  el.uploadBtn.disabled = false;
}

function clearFile() {
  state.file = null;
  el.fileInput.value = '';
  el.fileInfo.hidden = true;
  el.dropZone.hidden = false;
  el.uploadBtn.disabled = true;
}

/* ────────────────────────────────────────────
   Upload
──────────────────────────────────────────── */
async function uploadFile() {
  if (!state.file || state.isUploading) return;

  state.isUploading = true;
  el.uploadBtn.disabled = true;
  el.uploadBtn.classList.add('loading');
  el.uploadBtn.querySelector('.btn-text').textContent = 'Analysing…';
  setStatus('Uploading…', 'loading');

  const formData = new FormData();
  formData.append('file', state.file);

  try {
    const res = await fetch(API.UPLOAD, { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Upload failed.');
    }

    state.sessionId = data.session_id;
    el.sessionId.textContent = data.session_id.slice(0, 8) + '…';
    el.sessionBadge.hidden = false;

    // Enable chat
    el.questionInput.disabled = false;
    el.sendBtn.disabled = false;
    el.questionInput.focus();

    // Remove empty state
    el.chatEmpty.remove();

    setStatus('Document ready', 'active');
    showToast('Document analysed — ask your first question!', 'success');

  } catch (err) {
    showToast(err.message, 'error');
    setStatus('Upload failed', 'error');
    el.uploadBtn.disabled = false;
  } finally {
    state.isUploading = false;
    el.uploadBtn.classList.remove('loading');
    el.uploadBtn.querySelector('.btn-text').textContent = 'Analyse Document';
  }
}

/* ────────────────────────────────────────────
   Chat — Message Rendering
──────────────────────────────────────────── */
function appendMessage(role, content, id = null) {
  const wrap = document.createElement('div');
  wrap.className = `message ${role}`;
  if (id) wrap.dataset.messageId = id;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = role === 'user' ? 'U' : '◈';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';

  if (role === 'thinking') {
    wrap.className = 'message assistant thinking';
    bubble.innerHTML = `
      <div class="thinking-dots">
        <span></span><span></span><span></span>
      </div>`;
  } else {
    bubble.textContent = content;
  }

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  el.chatWindow.appendChild(wrap);
  el.chatWindow.scrollTop = el.chatWindow.scrollHeight;
  return wrap;
}

function updateMessage(messageEl, content) {
  const bubble = messageEl.querySelector('.message-bubble');
  bubble.textContent = content;
  messageEl.className = 'message assistant';
}

/* ────────────────────────────────────────────
   Chat — Send Question
──────────────────────────────────────────── */
async function sendQuestion() {
  const question = el.questionInput.value.trim();
  if (!question || state.isAsking || !state.sessionId) return;

  state.isAsking = true;
  el.sendBtn.disabled = true;
  el.questionInput.disabled = true;
  el.questionInput.value = '';
  setStatus('Thinking…', 'loading');

  // Show user message
  appendMessage('user', question);

  // Show thinking indicator
  const thinkingEl = appendMessage('thinking', '');

  let taskId = null;

  try {
    // 1. Submit question
    const askRes = await fetch(API.ASK, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id: state.sessionId, question }),
    });
    const askData = await askRes.json();
    if (!askRes.ok) throw new Error(askData.detail || 'Failed to queue question.');
    taskId = askData.task_id;

    // 2. Poll for answer
    const answer = await pollForAnswer(taskId);
    updateMessage(thinkingEl, answer);
    setStatus('Document ready', 'active');

  } catch (err) {
    if (thinkingEl.isConnected) {
      updateMessage(thinkingEl, `⚠ Error: ${err.message}`);
    }
    showToast(err.message, 'error');
    setStatus('Error', 'error');
  } finally {
    state.isAsking = false;
    el.sendBtn.disabled = false;
    el.questionInput.disabled = false;
    el.questionInput.focus();
  }
}

/* ────────────────────────────────────────────
   Long-Polling
──────────────────────────────────────────── */
async function pollForAnswer(taskId) {
  for (let attempt = 0; attempt < POLL_MAX_RETRIES; attempt++) {
    await sleep(POLL_INTERVAL_MS);

    const res = await fetch(`${API.ANSWER}/${taskId}`);
    const data = await res.json();

    if (data.status === 'SUCCESS') {
      if (data.error) throw new Error(data.error);
      return data.answer;
    }
    if (data.status === 'FAILURE') {
      throw new Error(data.error || 'Task failed on the server.');
    }
    // PENDING | STARTED — keep polling
  }
  throw new Error('Timed out waiting for an answer.');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/* ────────────────────────────────────────────
   Event Listeners
──────────────────────────────────────────── */
// Browse button
el.browseBtn.addEventListener('click', () => el.fileInput.click());
el.dropZone.addEventListener('click', () => el.fileInput.click());
el.dropZone.addEventListener('keydown', e => {
  if (e.key === 'Enter' || e.key === ' ') el.fileInput.click();
});

// File input
el.fileInput.addEventListener('change', e => {
  if (e.target.files[0]) applyFile(e.target.files[0]);
});

// Drag & Drop
el.dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  el.dropZone.classList.add('dragover');
});
['dragleave', 'dragend'].forEach(ev =>
  el.dropZone.addEventListener(ev, () => el.dropZone.classList.remove('dragover'))
);
el.dropZone.addEventListener('drop', e => {
  e.preventDefault();
  el.dropZone.classList.remove('dragover');
  if (e.dataTransfer.files[0]) applyFile(e.dataTransfer.files[0]);
});

// Remove file
el.removeFile.addEventListener('click', clearFile);

// Upload button
el.uploadBtn.addEventListener('click', uploadFile);

// Send question
el.sendBtn.addEventListener('click', sendQuestion);
el.questionInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    sendQuestion();
  }
});

// Auto-resize textarea
el.questionInput.addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});
