import initSqlJs from 'sql.js';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'fs';
import { v4 as uuidv4 } from 'uuid';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, '..', 'data', 'chat.db');

let db = null;
let SQL = null;

function getDbPath() {
  mkdirSync(join(__dirname, '..', 'data'), { recursive: true });
  return DB_PATH;
}

async function getDb() {
  if (db) return db;
  
  SQL = await initSqlJs();
  const dbPath = getDbPath();
  
  if (existsSync(dbPath)) {
    const buffer = readFileSync(dbPath);
    db = new SQL.Database(buffer);
  } else {
    db = new SQL.Database();
  }
  
  db.run('PRAGMA journal_mode = WAL');
  db.run('PRAGMA foreign_keys = ON');
  initSchema();
  saveDb();
  
  return db;
}

function saveDb() {
  if (db) {
    const data = db.export();
    const buffer = Buffer.from(data);
    writeFileSync(DB_PATH, buffer);
  }
}

function initSchema() {
  db.run(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      username TEXT UNIQUE NOT NULL,
      display_name TEXT NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'user',
      totp_secret TEXT,
      totp_enabled INTEGER DEFAULT 0,
      public_key TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      last_seen TEXT
    )
  `);
  db.run(`
    CREATE TABLE IF NOT EXISTS sessions (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      topic TEXT DEFAULT '',
      created_by TEXT NOT NULL REFERENCES users(id),
      is_encrypted INTEGER DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    )
  `);
  db.run(`
    CREATE TABLE IF NOT EXISTS session_participants (
      session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      user_id TEXT NOT NULL REFERENCES users(id),
      PRIMARY KEY (session_id, user_id)
    )
  `);
  db.run(`
    CREATE TABLE IF NOT EXISTS messages (
      id TEXT PRIMARY KEY,
      session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
      agent_id TEXT NOT NULL,
      sender_name TEXT NOT NULL,
      sender_role TEXT NOT NULL DEFAULT 'user',
      text TEXT NOT NULL,
      encrypted_text TEXT,
      encryption_iv TEXT,
      created_at TEXT DEFAULT (datetime('now'))
    )
  `);
  db.run(`
    CREATE TABLE IF NOT EXISTS refresh_tokens (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      token_hash TEXT NOT NULL,
      expires_at TEXT NOT NULL,
      created_at TEXT DEFAULT (datetime('now'))
    )
  `);
  
  try { db.run('CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)'); } catch {}
  try { db.run('CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(created_by)'); } catch {}
  try { db.run('CREATE INDEX IF NOT EXISTS idx_refresh_user ON refresh_tokens(user_id)'); } catch {}
}

function query(sql, params = []) {
  const stmt = db.prepare(sql);
  if (sql.trim().toUpperCase().startsWith('SELECT') || sql.trim().toUpperCase().startsWith('WITH')) {
    stmt.bind(params);
    const rows = [];
    while (stmt.step()) {
      rows.push(stmt.getAsObject());
    }
    stmt.free();
    return rows;
  } else {
    if (params.length > 0) stmt.bind(params);
    stmt.step();
    stmt.free();
    saveDb();
    return { changes: db.getRowsModified() };
  }
}

function run(sql, params = []) {
  try {
    db.run(sql, params);
    saveDb();
  } catch (e) {
    console.error('DB run error:', e.message);
    throw e;
  }
}

// ======== USERS ========
export function createUser({ username, displayName, passwordHash, role = 'user' }) {
  const id = uuidv4();
  run('INSERT INTO users (id, username, display_name, password_hash, role) VALUES (?, ?, ?, ?, ?)',
    [id, username, displayName, passwordHash, role]);
  return { id, username, displayName, role };
}

export function getUserByUsername(username) {
  const rows = query('SELECT * FROM users WHERE username = ?', [username]);
  return rows[0] || null;
}

export function getUser(id) {
  const rows = query('SELECT id, username, display_name, role, totp_enabled, public_key, created_at, last_seen FROM users WHERE id = ?', [id]);
  return rows[0] || null;
}

export function updateUserTotp(userId, secret) {
  run('UPDATE users SET totp_secret = ?, totp_enabled = 1 WHERE id = ?', [secret, userId]);
}

export function getUserTotpSecret(userId) {
  const rows = query('SELECT totp_secret FROM users WHERE id = ?', [userId]);
  return rows[0]?.totp_secret || null;
}

export function getAllUsers(excludeId) {
  return query(`SELECT id, username, display_name FROM users WHERE id != ? ORDER BY display_name`, [excludeId]);
}

export function getSessionParticipants(sessionId) {
  return query(`
    SELECT u.id, u.username, u.display_name
    FROM session_participants sp JOIN users u ON sp.user_id = u.id
    WHERE sp.session_id = ?
  `, [sessionId]);
}

export function updateUserPublicKey(userId, key) {
  run('UPDATE users SET public_key = ? WHERE id = ?', [key, userId]);
}

export function updateUserLastSeen(userId) {
  run("UPDATE users SET last_seen = datetime('now') WHERE id = ?", [userId]);
}

// ======== SESSIONS ========
export function createSession({ title, topic, createdBy }) {
  const id = uuidv4();
  run('INSERT INTO sessions (id, title, topic, created_by) VALUES (?, ?, ?, ?)', [id, title, topic || '', createdBy]);
  run('INSERT INTO session_participants (session_id, user_id) VALUES (?, ?)', [id, createdBy]);
  return { id, title, topic };
}

export function getSessions(userId) {
  return query(`
    SELECT s.*, u.display_name as creator_name,
      (SELECT COUNT(*) FROM messages WHERE session_id = s.id) as msg_count
    FROM sessions s JOIN users u ON s.created_by = u.id
    WHERE s.id IN (SELECT session_id FROM session_participants WHERE user_id = ?)
    ORDER BY s.updated_at DESC
  `, [userId]);
}

export function getSession(id) {
  const rows = query('SELECT * FROM sessions WHERE id = ?', [id]);
  return rows[0] || null;
}

export function updateSessionTitle(id, title) {
  run("UPDATE sessions SET title = ?, updated_at = datetime('now') WHERE id = ?", [title, id]);
}

export function deleteSession(id) {
  run('DELETE FROM messages WHERE session_id = ?', [id]);
  run('DELETE FROM session_participants WHERE session_id = ?', [id]);
  run('DELETE FROM sessions WHERE id = ?', [id]);
}

export function addParticipant(sessionId, userId) {
  try {
    run('INSERT INTO session_participants (session_id, user_id) VALUES (?, ?)', [sessionId, userId]);
  } catch {}
}

// ======== MESSAGES ========
export function getMessages(sessionId, limit = 100) {
  return query(
    'SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?',
    [sessionId, limit]
  );
}

export function saveMessage({ sessionId, agentId, senderName, senderRole = 'user', text, encryptedText, encryptionIv }) {
  const id = uuidv4();
  run(`INSERT INTO messages (id, session_id, agent_id, sender_name, sender_role, text, encrypted_text, encryption_iv) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    [id, sessionId, agentId, senderName, senderRole, text, encryptedText || null, encryptionIv || null]);
  run("UPDATE sessions SET updated_at = datetime('now') WHERE id = ?", [sessionId]);
  return { id, sessionId, agentId, senderName, senderRole, text, createdAt: new Date().toISOString() };
}

// ======== REFRESH TOKENS ========
export function saveRefreshToken(userId, tokenHash, expiresAt) {
  const id = uuidv4();
  run('INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at) VALUES (?, ?, ?, ?)', [id, userId, tokenHash, expiresAt]);
}

export function deleteRefreshToken(tokenHash) {
  run('DELETE FROM refresh_tokens WHERE token_hash = ?', [tokenHash]);
}

export function getRefreshToken(tokenHash) {
  const rows = query('SELECT * FROM refresh_tokens WHERE token_hash = ?', [tokenHash]);
  return rows[0] || null;
}

export function cleanupExpiredTokens() {
  run("DELETE FROM refresh_tokens WHERE expires_at < datetime('now')");
}

export { getDb };
