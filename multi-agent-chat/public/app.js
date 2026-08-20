// ======== STATE ========
const state = {
  user: null,
  accessToken: null,
  refreshToken: null,
  sessions: [],
  currentSessionId: null,
  agents: [],
  ws: null,
  typingTimers: {},
};

// ======== API ========
const API = {
  async request(method, path, body) {
    const headers = { 'Content-Type': 'application/json' };
    if (state.accessToken) {
      headers['Authorization'] = `Bearer ${state.accessToken}`;
    }
    const res = await fetch(`/api${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
    if (res.status === 401) {
      // Try refresh
      const refreshed = await API.refresh();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${state.accessToken}`;
        const retry = await fetch(`/api${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
        return retry.json();
      }
      showAuth();
      return null;
    }
    return res.json();
  },
  async refresh() {
    if (!state.refreshToken) return false;
    const res = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken: state.refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    state.accessToken = data.accessToken;
    state.refreshToken = data.refreshToken;
    saveTokens();
    return true;
  },
  login(username, password, totpToken) {
    return fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, totpToken }),
    }).then(r => r.json());
  },
  register(username, displayName, password) {
    return fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, displayName, password }),
    }).then(r => r.json());
  },
  getSessions() { return API.request('GET', '/sessions'); },
  createSession(title, topic) { return API.request('POST', '/sessions', { title, topic }); },
  getSession(id) { return API.request('GET', `/sessions/${id}`); },
  getMessages(id) { return API.request('GET', `/sessions/${id}/messages`); },
  deleteSession(id) { return API.request('DELETE', `/sessions/${id}`); },
  setup2fa(userId) { return API.request('POST', '/auth/setup-2fa', { userId }); },
};

// ======== TOKENS ========
function saveTokens() {
  localStorage.setItem('accessToken', state.accessToken);
  localStorage.setItem('refreshToken', state.refreshToken);
}

function loadTokens() {
  state.accessToken = localStorage.getItem('accessToken');
  state.refreshToken = localStorage.getItem('refreshToken');
}

function clearTokens() {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
}

// ======== AUTH ========
function showAuth() {
  document.getElementById('auth-screen').classList.remove('hidden');
  document.getElementById('main-screen').classList.add('hidden');
  clearTokens();
  if (state.ws) { state.ws.close(); state.ws = null; }
}

function showMain() {
  document.getElementById('auth-screen').classList.add('hidden');
  document.getElementById('main-screen').classList.remove('hidden');
}

// ======== WEBSOCKET ========
function connectWS() {
  if (state.ws) state.ws.close();
  const ws = new WebSocket(`${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/ws?token=${state.accessToken}`);
  state.ws = ws;

  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    switch (data.type) {
      case 'init':
        state.agents = data.agents;
        break;
      case 'message':
        handleIncomingMessage(data);
        break;
      case 'typing':
        showTyping(data.agentId);
        break;
      case 'typing-end':
        hideTyping(data.agentId);
        break;
    }
  };

  ws.onclose = () => {
    setTimeout(connectWS, 3000);
  };
}

// ======== MESSAGES ========
function handleIncomingMessage(data) {
  if (data.sessionId !== state.currentSessionId) {
    // Update sidebar badge
    updateSessionBadge(data.sessionId);
    return;
  }
  hideTyping(data.agentId);
  appendMessage(data);
}

function appendMessage(data) {
  const container = document.getElementById('messages');
  const agent = state.agents.find(a => a.id === data.agentId);
  const div = document.createElement('div');
  div.className = `msg ${data.senderRole === 'user' ? 'user' : 'agent'}`;
  div.dataset.msgId = data.id;

  if (data.senderRole === 'agent') {
    div.style.background = `${agent?.color || '#6366f1'}22`;
    div.style.border = `1px solid ${agent?.color || '#6366f1'}44`;
  }

  const time = new Date(data.createdAt || Date.now()).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

  div.innerHTML = `
    <div class="meta">${agent?.emoji || ''} ${data.senderName}</div>
    <div class="msg-content">${escapeHtml(data.text)}</div>
    <div class="time">${time}</div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

// ======== TYPING ========
function showTyping(agentId) {
  const container = document.getElementById('typing-indicators');
  if (document.getElementById(`typing-${agentId}`)) return;
  const agent = state.agents.find(a => a.id === agentId);
  if (!agent) return;
  const el = document.createElement('span');
  el.id = `typing-${agentId}`;
  el.className = 'typing-dot';
  el.innerHTML = `
    <span style="color:${agent.color}">${agent.emoji}</span>
    <span class="dot" style="background:${agent.color}"></span>
    <span class="dot" style="background:${agent.color}"></span>
    <span class="dot" style="background:${agent.color}"></span>
  `;
  container.appendChild(el);
}

function hideTyping(agentId) {
  const el = document.getElementById(`typing-${agentId}`);
  if (el) el.remove();
}

// ======== SESSIONS ========
async function loadSessions() {
  const sessions = await API.getSessions();
  if (!sessions) return;
  state.sessions = sessions;
  renderSidebar();
}

function renderSidebar() {
  const list = document.getElementById('chat-list');
  list.innerHTML = '';
  state.sessions.forEach(s => {
    const div = document.createElement('div');
    div.className = `chat-item${s.id === state.currentSessionId ? ' active' : ''}`;
    div.dataset.sessionId = s.id;
    div.innerHTML = `
      <div class="chat-item-icon">💬</div>
      <div class="chat-item-info">
        <div class="chat-item-title">${escapeHtml(s.title)}</div>
        <div class="chat-item-meta">${s.msg_count || 0} сообщ. · ${s.topic || 'без темы'}</div>
      </div>
    `;
    div.onclick = () => openSession(s.id);
    list.appendChild(div);
  });
}

function updateSessionBadge(sessionId) {
  // Highlight in sidebar
  const item = document.querySelector(`.chat-item[data-session-id="${sessionId}"]`);
  if (item) {
    item.style.opacity = '0.7';
    setTimeout(() => { item.style.opacity = '1'; }, 1000);
  }
}

async function openSession(id) {
  state.currentSessionId = id;
  document.getElementById('empty-state').classList.add('hidden');
  document.getElementById('chat-view').classList.remove('hidden');

  // Update sidebar
  document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
  const active = document.querySelector(`.chat-item[data-session-id="${id}"]`);
  if (active) active.classList.add('active');

  // Load messages
  const data = await API.getSession(id);
  if (!data) return;

  document.getElementById('chat-title').textContent = data.session.title;
  document.getElementById('chat-topic').textContent = data.session.topic || '';

  const container = document.getElementById('messages');
  container.innerHTML = '';
  data.messages.forEach(m => {
    appendMessage({
      id: m.id,
      agentId: m.agent_id,
      senderName: m.sender_name,
      senderRole: m.sender_role,
      text: m.text,
      createdAt: m.created_at,
    });
  });
  container.scrollTop = container.scrollHeight;
}

async function createNewChat() {
  const title = prompt('Название чата:', 'Новый чат');
  if (!title) return;
  const topic = prompt('Тема (опционально):', '');
  const session = await API.createSession(title, topic || '');
  if (session) {
    state.sessions.unshift(session);
    renderSidebar();
    openSession(session.id);
  }
}

// ======== SEND MESSAGE ========
function sendMessage() {
  const input = document.getElementById('message-input');
  const text = input.value.trim();
  if (!text || !state.currentSessionId || !state.ws) return;

  input.value = '';
  state.ws.send(JSON.stringify({
    type: 'message',
    sessionId: state.currentSessionId,
    text,
  }));
}

// ======== 2FA ========
async function setup2FA() {
  if (!state.user) return;
  const data = await API.setup2fa(state.user.id);
  if (!data) return;
  document.getElementById('2fa-qr').innerHTML = `<img src="${data.qrCode}" alt="QR Code">`;
  document.getElementById('2fa-secret').textContent = data.secret;
  document.getElementById('2fa-setup').classList.remove('hidden');
  document.getElementById('enable-2fa-btn').textContent = '✅ 2FA включён';
  document.getElementById('enable-2fa-btn').disabled = true;
}

// ======== INIT ========
async function init() {
  loadTokens();

  // Check for existing session
  if (state.accessToken) {
    const refreshed = await API.refresh();
    if (refreshed) {
      showMain();
      connectWS();
      loadSessions();
      return;
    }
  }

  showAuth();
}

// ======== DOM EVENTS ========
document.addEventListener('DOMContentLoaded', () => {
  init();

  // Auth tabs
  document.querySelectorAll('.auth-tab').forEach(tab => {
    tab.onclick = () => {
      document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const isLogin = tab.dataset.tab === 'login';
      document.getElementById('login-form').classList.toggle('hidden', !isLogin);
      document.getElementById('register-form').classList.toggle('hidden', isLogin);
    };
  });

  // Login form
  document.getElementById('login-form').onsubmit = async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const totpToken = document.getElementById('login-totp').value;

    const data = await API.login(username, password, totpToken);
    if (data.error) {
      const err = document.getElementById('login-error');
      err.textContent = data.error;
      err.classList.remove('hidden');
      if (data.requireTotp) {
        document.getElementById('totp-group').classList.remove('hidden');
      }
      return;
    }

    state.user = data.user;
    state.accessToken = data.accessToken;
    state.refreshToken = data.refreshToken;
    saveTokens();
    document.getElementById('user-name').textContent = data.user.displayName;

    showMain();
    connectWS();
    loadSessions();
  };

  // Register form
  document.getElementById('register-form').onsubmit = async (e) => {
    e.preventDefault();
    const username = document.getElementById('reg-username').value;
    const displayName = document.getElementById('reg-displayname').value || username;
    const password = document.getElementById('reg-password').value;

    const data = await API.register(username, displayName, password);
    if (data.error) {
      document.getElementById('reg-error').textContent = data.error;
      document.getElementById('reg-error').classList.remove('hidden');
      return;
    }

    state.user = data.user;
    state.accessToken = data.accessToken;
    state.refreshToken = data.refreshToken;
    saveTokens();
    document.getElementById('user-name').textContent = data.user.displayName;

    showMain();
    connectWS();
    loadSessions();
  };

  // Send message
  document.getElementById('send-btn').onclick = sendMessage;
  document.getElementById('message-input').onkeydown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // New chat
  document.getElementById('new-chat-btn').onclick = createNewChat;
  document.getElementById('empty-new-chat').onclick = createNewChat;

  // Logout
  document.getElementById('logout-btn').onclick = () => {
    if (state.ws) state.ws.close();
    state.user = null;
    state.accessToken = null;
    state.refreshToken = null;
    state.currentSessionId = null;
    clearTokens();
    showAuth();
  };

  // Settings modal
  document.getElementById('settings-btn').onclick = () => {
    document.getElementById('settings-modal').classList.remove('hidden');
  };
  document.querySelector('#settings-modal .modal-close').onclick = () => {
    document.getElementById('settings-modal').classList.add('hidden');
  };
  document.querySelector('#settings-modal .modal-backdrop').onclick = () => {
    document.getElementById('settings-modal').classList.add('hidden');
  };

  // 2FA setup
  document.getElementById('enable-2fa-btn').onclick = setup2FA;

  // Delete chat
  document.getElementById('chat-delete-btn').onclick = async () => {
    if (!state.currentSessionId) return;
    if (!confirm('Удалить этот чат?')) return;
    await API.deleteSession(state.currentSessionId);
    state.currentSessionId = null;
    document.getElementById('chat-view').classList.add('hidden');
    document.getElementById('empty-state').classList.remove('hidden');
    loadSessions();
  };

  // Search chats
  document.getElementById('search-chats').oninput = (e) => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('.chat-item').forEach(el => {
      const title = el.querySelector('.chat-item-title')?.textContent?.toLowerCase() || '';
      el.style.display = title.includes(q) ? 'flex' : 'none';
    });
  };
});

// ======== E2E ENCRYPTION ========
let isEncryptionEnabled = false;

async function generateKeys() {
  const keyPair = await generateKeyPair();
  setUserKeyPair(keyPair);
  
  // Send public key to server
  const res = await fetch('/api/sessions/update-key', {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${state.accessToken}`
    },
    body: JSON.stringify({ publicKey: keyPair.publicKey }),
  });
  
  if (res.ok) {
    document.getElementById('keys-status').textContent = '✅ RSA-4096 ключи сгенерированы и сохранены';
    state.user.publicKey = keyPair.publicKey;
  }
}

async function toggleEncryption() {
  isEncryptionEnabled = !isEncryptionEnabled;
  const btn = document.getElementById('chat-encrypt-btn');
  btn.textContent = isEncryptionEnabled ? '🔐' : '🔒';
  btn.style.color = isEncryptionEnabled ? '#22c55e' : '';
  
  if (isEncryptionEnabled) {
    // Generate a session key for this chat
    const sessionKey = await generateSessionKey();
    setSessionKey(state.currentSessionId, sessionKey);
    console.log('🔐 E2E encryption enabled for this session');
  }
}

// Override sendMessage to encrypt
const originalSendMessage = sendMessage;
sendMessage = async function() {
  const input = document.getElementById('message-input');
  const text = input.value.trim();
  if (!text || !state.currentSessionId || !state.ws) return;
  
  input.value = '';
  
  if (isEncryptionEnabled) {
    const sessionKey = getSessionKey(state.currentSessionId);
    if (sessionKey) {
      const encrypted = await encryptMessage(text, sessionKey.key);
      state.ws.send(JSON.stringify({
        type: 'message',
        sessionId: state.currentSessionId,
        text: text,
        encryptedText: encrypted.ciphertext,
        encryptionIv: encrypted.iv,
      }));
      return;
    }
  }
  
  state.ws.send(JSON.stringify({
    type: 'message',
    sessionId: state.currentSessionId,
    text,
  }));
};

// Add event listeners for E2E
document.addEventListener('DOMContentLoaded', () => {
  const existing = document.getElementById('gen-keys-btn');
  if (existing) existing.onclick = generateKeys;
  
  const encryptBtn = document.getElementById('chat-encrypt-btn');
  if (encryptBtn) encryptBtn.onclick = toggleEncryption;
  
  // Check if user already has keys
  const existingKeys = getUserKeyPair();
  if (existingKeys) {
    document.getElementById('keys-status').textContent = '✅ Ключи загружены из сессии';
  }
});

// ======== INVITE ========
async function openInviteModal() {
  const modal = document.getElementById('invite-modal');
  const select = document.getElementById('invite-user-select');
  const err = document.getElementById('invite-error');
  err.classList.add('hidden');
  
  select.innerHTML = '<option value="">Загрузка...</option>';
  modal.classList.remove('hidden');
  
  // Get users
  const users = await API.request('GET', '/sessions/users');
  if (!users || users.length === 0) {
    select.innerHTML = '<option value="">Нет других пользователей</option>';
    return;
  }
  
  // Get current participants
  const participants = await API.request('GET', `/sessions/${state.currentSessionId}/participants`);
  const participantIds = new Set((participants || []).map(p => p.id));
  
  select.innerHTML = '<option value="">-- Выберите --</option>';
  users.forEach(u => {
    if (!participantIds.has(u.id)) {
      const opt = document.createElement('option');
      opt.value = u.id;
      opt.textContent = `${u.display_name} (@${u.username})`;
      select.appendChild(opt);
    }
  });
  
  if (select.options.length === 1) {
    select.innerHTML = '<option value="">Все уже в чате</option>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Invite button
  document.getElementById('chat-invite-btn').onclick = openInviteModal;
  
  // Invite modal close
  const inviteModal = document.getElementById('invite-modal');
  inviteModal.querySelector('.modal-close').onclick = () => inviteModal.classList.add('hidden');
  inviteModal.querySelector('.modal-backdrop').onclick = () => inviteModal.classList.add('hidden');
  
  // Invite submit
  document.getElementById('invite-submit-btn').onclick = async () => {
    const select = document.getElementById('invite-user-select');
    const userId = select.value;
    const err = document.getElementById('invite-error');
    
    if (!userId) {
      err.textContent = 'Выберите пользователя';
      err.classList.remove('hidden');
      return;
    }
    
    const res = await fetch(`/api/sessions/${state.currentSessionId}/invite`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.accessToken}`
      },
      body: JSON.stringify({ userId }),
    });
    
    if (res.ok) {
      inviteModal.classList.add('hidden');
      select.value = '';
      // Remove invited user from dropdown
      const opt = select.querySelector(`option[value="${userId}"]`);
      if (opt) opt.remove();
    } else {
      const data = await res.json();
      err.textContent = data.error || 'Ошибка приглашения';
      err.classList.remove('hidden');
    }
  };
});
