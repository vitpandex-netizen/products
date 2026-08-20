import { Router } from 'express';
import {
  createSession, getSessions, getSession, getMessages,
  updateSessionTitle, deleteSession, addParticipant,
  updateUserPublicKey, getAllUsers, getSessionParticipants
} from '../db.js';
import { authMiddleware } from '../auth.js';

const router = Router();

router.use(authMiddleware);

router.get('/', (req, res) => {
  const sessions = getSessions(req.user.sub);
  res.json(sessions);
});

router.post('/', (req, res) => {
  const { title, topic } = req.body;
  const session = createSession({
    title: title || 'Новый чат',
    topic: topic || '',
    createdBy: req.user.sub,
  });
  res.status(201).json(session);
});

router.get('/users', (req, res) => {
  const users = getAllUsers(req.user.sub);
  res.json(users);
});

router.get('/:id', (req, res) => {
  const session = getSession(req.params.id);
  if (!session) return res.status(404).json({ error: 'Session not found' });
  const messages = getMessages(req.params.id);
  const participants = getSessionParticipants(req.params.id);
  res.json({ session, messages, participants });
});

router.get('/:id/participants', (req, res) => {
  const participants = getSessionParticipants(req.params.id);
  res.json(participants);
});

router.get('/:id/messages', (req, res) => {
  const messages = getMessages(req.params.id);
  res.json(messages);
});

router.put('/:id', (req, res) => {
  const { title } = req.body;
  updateSessionTitle(req.params.id, title);
  res.json({ ok: true });
});

router.delete('/:id', (req, res) => {
  deleteSession(req.params.id);
  res.json({ ok: true });
});

router.post('/:id/join', (req, res) => {
  addParticipant(req.params.id, req.user.sub);
  res.json({ ok: true });
});

// Invite user to session
router.post('/:id/invite', (req, res) => {
  const { userId } = req.body;
  if (!userId) return res.status(400).json({ error: 'userId required' });

  const session = getSession(req.params.id);
  if (!session) return res.status(404).json({ error: 'Session not found' });

  // Only creator or admin can invite
  if (session.created_by !== req.user.sub && req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Only creator or admin can invite' });
  }

  addParticipant(req.params.id, userId);
  res.json({ ok: true });
});

// Update public key for E2E
router.post('/update-key', (req, res) => {
  const { publicKey } = req.body;
  if (!publicKey) return res.status(400).json({ error: 'Public key required' });
  updateUserPublicKey(req.user.sub, publicKey);
  res.json({ ok: true });
});

export default router;
