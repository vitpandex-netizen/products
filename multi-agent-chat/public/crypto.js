// ======== E2E Encryption Module ========
// Использует Web Crypto API для шифрования сообщений

const CRYPTO_KEY = 'multi-agent-chat-e2e';

export async function generateKeyPair() {
  const keyPair = await crypto.subtle.generateKey(
    {
      name: 'RSA-OAEP',
      modulusLength: 4096,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: 'SHA-256',
    },
    true,
    ['encrypt', 'decrypt']
  );

  // Export public key for server
  const publicKeySpki = await crypto.subtle.exportKey('spki', keyPair.publicKey);
  const publicKeyB64 = arrayBufferToBase64(publicKeySpki);

  // Export private key for storage
  const privateKeyPkcs8 = await crypto.subtle.exportKey('pkcs8', keyPair.privateKey);
  const privateKeyB64 = arrayBufferToBase64(privateKeyPkcs8);

  return { publicKey: publicKeyB64, privateKey: privateKeyB64 };
}

export async function importPrivateKey(privateKeyB64) {
  const privateKeyBuffer = base64ToArrayBuffer(privateKeyB64);
  return await crypto.subtle.importKey(
    'pkcs8',
    privateKeyBuffer,
    { name: 'RSA-OAEP', hash: 'SHA-256' },
    false,
    ['decrypt']
  );
}

export async function importPublicKey(publicKeyB64) {
  const publicKeyBuffer = base64ToArrayBuffer(publicKeyB64);
  return await crypto.subtle.importKey(
    'spki',
    publicKeyBuffer,
    { name: 'RSA-OAEP', hash: 'SHA-256' },
    false,
    ['encrypt']
  );
}

// Generate a symmetric AES-GCM key for a session
export async function generateSessionKey() {
  const key = await crypto.subtle.generateKey(
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );
  const raw = await crypto.subtle.exportKey('raw', key);
  return { key, raw: arrayBufferToBase64(raw) };
}

// Import AES-GCM key from raw base64
export async function importSessionKey(rawB64) {
  const raw = base64ToArrayBuffer(rawB64);
  return await crypto.subtle.importKey('raw', raw, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']);
}

// Encrypt session key with user's RSA public key
export async function encryptSessionKey(sessionKeyRaw, publicKeyB64) {
  const publicKey = await importPublicKey(publicKeyB64);
  const data = new TextEncoder().encode(sessionKeyRaw);
  const encrypted = await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, publicKey, data);
  return arrayBufferToBase64(encrypted);
}

// Decrypt session key with user's RSA private key
export async function decryptSessionKey(encryptedB64, privateKeyB64) {
  const privateKey = await importPrivateKey(privateKeyB64);
  const encrypted = base64ToArrayBuffer(encryptedB64);
  const decrypted = await crypto.subtle.decrypt({ name: 'RSA-OAEP' }, privateKey, encrypted);
  return new TextDecoder().decode(decrypted);
}

// Encrypt a message with AES-GCM session key
export async function encryptMessage(text, sessionKey) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(text);
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    sessionKey,
    encoded
  );
  return {
    ciphertext: arrayBufferToBase64(encrypted),
    iv: arrayBufferToBase64(iv),
  };
}

// Decrypt a message with AES-GCM session key
export async function decryptMessage(ciphertextB64, ivB64, sessionKey) {
  const ciphertext = base64ToArrayBuffer(ciphertextB64);
  const iv = base64ToArrayBuffer(ivB64);
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv },
    sessionKey,
    ciphertext
  );
  return new TextDecoder().decode(decrypted);
}

// Session key store (per chat session)
const sessionKeyStore = new Map();

export function setSessionKey(sessionId, key) {
  sessionKeyStore.set(sessionId, key);
}

export function getSessionKey(sessionId) {
  return sessionKeyStore.get(sessionId);
}

// Store user's own key pair
let userKeyPair = null;

export function setUserKeyPair(keyPair) {
  userKeyPair = keyPair;
  sessionStorage.setItem(CRYPTO_KEY, JSON.stringify(keyPair));
}

export function getUserKeyPair() {
  if (userKeyPair) return userKeyPair;
  const stored = sessionStorage.getItem(CRYPTO_KEY);
  if (stored) {
    try {
      userKeyPair = JSON.parse(stored);
      return userKeyPair;
    } catch {}
  }
  return null;
}

export function clearUserKeyPair() {
  userKeyPair = null;
  sessionStorage.removeItem(CRYPTO_KEY);
}

// Helpers
function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64ToArrayBuffer(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}
