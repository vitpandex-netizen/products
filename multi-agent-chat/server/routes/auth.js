import { Router } from 'express';
import crypto from 'crypto';
import speakeasy from 'speakeasy';
import qrcode from 'qrcode';
import {
  createUser, getUserByUsername, getUser, updateUserTotp, getUserTotpSecret,
  updateUserPublicKey, updateUserLastSeen, saveRefreshToken, deleteRefreshToken, getRefreshToken
} from '../db.js';
import { hashPassword, verifyPassword, generateAccessToken, generateRefreshToken } from '../auth.js';

const router = Router();

router.post('/register', async (req, res) => {
  try {
    const { username, displayName, password, role } = req.body;
    if (!username || !password) return res.status(400).json({ error: 'Username and password required' });

    const existing = getUserByUsername(username);
    if (existing) return res.status(409).json({ error: 'Username already exists' });

    const user = createUser({
      username,
      displayName: displayName || username,
      passwordHash: hashPassword(password),
      role: role || 'user',
    });

    const accessToken = generateAccessToken(user);
    const rt = generateRefreshToken();
    saveRefreshToken(user.id, rt.hash, rt.expiresAt);

    res.status(201).json({
      user: { id: user.id, username: user.username, displayName: user.displayName, role: user.role },
      accessToken,
      refreshToken: rt.token,
    });
  } catch (err) {
    console.error('Register error:', err);
    res.status(500).json({ error: 'Internal error' });
  }
});

router.post('/login', (req, res) => {
  try {
    const { username, password, totpToken } = req.body;
    if (!username || !password) return res.status(400).json({ error: 'Username and password required' });

    const user = getUserByUsername(username);
    if (!user) return res.status(401).json({ error: 'Invalid credentials' });

    if (!verifyPassword(password, user.password_hash)) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    if (user.totp_enabled) {
      if (!totpToken) return res.status(200).json({ requireTotp: true });
      const secret = getUserTotpSecret(user.id);
      const verified = speakeasy.totp.verify({
        secret,
        encoding: 'base32',
        token: totpToken,
        window: 1,
      });
      if (!verified) return res.status(401).json({ error: 'Invalid 2FA code' });
    }

    updateUserLastSeen(user.id);

    const accessToken = generateAccessToken(user);
    const rt = generateRefreshToken();
    saveRefreshToken(user.id, rt.hash, rt.expiresAt);

    res.json({
      user: {
        id: user.id,
        username: user.username,
        displayName: user.display_name,
        role: user.role,
        totpEnabled: !!user.totp_enabled,
        publicKey: user.public_key,
      },
      accessToken,
      refreshToken: rt.token,
    });
  } catch (err) {
    console.error('Login error:', err);
    res.status(500).json({ error: 'Internal error' });
  }
});

router.post('/refresh', (req, res) => {
  try {
    const { refreshToken } = req.body;
    if (!refreshToken) return res.status(400).json({ error: 'Refresh token required' });

    const hash = crypto.createHash('sha256').update(refreshToken).digest('hex');
    const stored = getRefreshToken(hash);
    if (!stored) return res.status(401).json({ error: 'Invalid refresh token' });

    deleteRefreshToken(hash);

    const user = getUser(stored.user_id);
    if (!user) return res.status(401).json({ error: 'User not found' });

    const accessToken = generateAccessToken(user);
    const rt = generateRefreshToken();
    saveRefreshToken(user.id, rt.hash, rt.expiresAt);

    res.json({ accessToken, refreshToken: rt.token });
  } catch (err) {
    console.error('Refresh error:', err);
    res.status(500).json({ error: 'Internal error' });
  }
});

router.post('/logout', (req, res) => {
  try {
    const { refreshToken } = req.body;
    if (refreshToken) {
      const hash = crypto.createHash('sha256').update(refreshToken).digest('hex');
      deleteRefreshToken(hash);
    }
    res.json({ ok: true });
  } catch (err) {
    res.status(500).json({ error: 'Internal error' });
  }
});

router.post('/setup-2fa', async (req, res) => {
  try {
    const { userId } = req.body;
    const secret = speakeasy.generateSecret({ name: `Multi-Agent Chat (${userId})` });
    updateUserTotp(userId, secret.base32);

    const qrUrl = await qrcode.toDataURL(secret.otpauth_url);

    res.json({
      secret: secret.base32,
      qrCode: qrUrl,
    });
  } catch (err) {
    console.error('2FA setup error:', err);
    res.status(500).json({ error: 'Internal error' });
  }
});

export default router;
