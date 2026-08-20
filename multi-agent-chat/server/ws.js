import { WebSocketServer } from 'ws';
import { getMessages, saveMessage, getSession, addParticipant } from './db.js';
import { callAllAgents, AGENTS } from './agents/index.js';
import { wsAuthMiddleware } from './auth.js';

export function setupWebSocket(server) {
  const wss = new WebSocketServer({ server, path: '/ws' });
  const clients = new Map();

  wss.on('connection', (ws, req) => {
    let userId = null;
    let userName = 'Anonymous';

    const url = new URL(req.url, 'http://localhost');
    const token = url.searchParams.get('token');
    if (token) {
      const payload = wsAuthMiddleware(token);
      if (payload) {
        userId = payload.sub;
        userName = payload.username || payload.sub;
      }
    }

    const clientId = Math.random().toString(36).slice(2);
    clients.set(clientId, { ws, userId, userName });

    ws.send(JSON.stringify({
      type: 'init',
      agents: AGENTS,
      clientId,
    }));

    ws.on('message', async (raw) => {
      let data;
      try {
        data = JSON.parse(raw.toString());
      } catch {
        return;
      }

      if (data.type === 'message') {
        const { sessionId, text } = data;
        if (!sessionId || !text) return;

        const session = getSession(sessionId);
        if (!session) return;

        // Save user message
        const userMsg = saveMessage({
          sessionId,
          agentId: 'user',
          senderName: userName,
          senderRole: 'user',
          text,
        });

        broadcast({
          type: 'message',
          ...userMsg,
          senderName: userName,
          senderRole: 'user',
          agentId: 'user',
        });

        // Get conversation history
        const history = getMessages(sessionId, 50);
        const context = session.topic || '';

        // Show typing indicators for all agents
        const agentIds = AGENTS.map(a => a.id);
        agentIds.forEach(aid => {
          broadcast({ type: 'typing', sessionId, agentId: aid });
        });

        // ONE API call — generates all 6 agent responses at once
        const apiKey = process.env.OPENROUTER_API_KEY;
        const responses = await callAllAgents(history, context, apiKey);

        // Send each agent's response with stagger
        for (const aid of agentIds) {
          const content = responses[aid];
          if (content && content.trim()) {
            const agent = AGENTS.find(a => a.id === aid);
            const agentMsg = saveMessage({
              sessionId,
              agentId: aid,
              senderName: agent?.name || aid,
              senderRole: 'agent',
              text: content,
            });

            broadcast({
              type: 'message',
              ...agentMsg,
              senderName: agent?.name || aid,
              senderRole: 'agent',
              agentId: aid,
            });

            // Stagger so they appear one by one
            await new Promise(r => setTimeout(r, 400));
          }

          // Clear typing for this agent
          broadcast({ type: 'typing-end', sessionId, agentId: aid });
        }
      }

      if (data.type === 'join') {
        const { sessionId } = data;
        if (sessionId && userId) {
          addParticipant(sessionId, userId);
        }
      }
    });

    ws.on('close', () => {
      clients.delete(clientId);
    });
  });

  function broadcast(msg) {
    const raw = JSON.stringify(msg);
    for (const [id, client] of clients) {
      if (client.ws.readyState === 1) {
        client.ws.send(raw);
      }
    }
  }

  return wss;
}
