import 'dotenv/config';
import express from 'express';
import { createServer as createHttpsServer } from 'https';
import { createServer as createHttpServer } from 'http';
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import helmet from 'helmet';
import cors from 'cors';
import { setupWebSocket } from './ws.js';
import authRoutes from './routes/auth.js';
import portalRoutes from "./portal.js";
import sessionRoutes from './routes/sessions.js';
import { cleanupExpiredTokens, getDb } from './db.js';
import { authLimiter, apiLimiter, globalLimiter } from './rateLimit.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = parseInt(process.env.PORT || '5555');
const INTERNAL_PORT = parseInt(process.env.INTERNAL_PORT || '5556');
const BEHIND_PROXY = process.env.BEHIND_PROXY === 'true';

async function main() {
  await getDb();
  console.log('✅ Database connected');

  const app = express();

  // Security headers (relaxed behind proxy, Caddy handles CSP)
  if (!BEHIND_PROXY) {
    app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'", "'unsafe-inline'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          imgSrc: ["'self'", "data:", "blob:"],
          connectSrc: ["'self'", "ws:", "wss:"],
        },
      },
      hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
    }));
  } else {
    app.use(helmet({ contentSecurityPolicy: false, hsts: false }));
  }

  app.set("trust proxy", BEHIND_PROXY ? 1 : 0);

app.use(cors({
    origin: process.env.CORS_ORIGIN || '*',
    credentials: true,
  }));

  app.use(express.json({ limit: '10mb' }));

  });

  // Global rate limiter
  app.use(globalLimiter);

  // Static files
  app.use(express.static(join(__dirname, '..', 'public')));

  // API routes
  app.use('/api/auth', authLimiter, authRoutes);
  app.use('/api/portal', portalRoutes);
app.use('/api/sessions', apiLimiter, sessionRoutes);

  });

  // Create HTTP server (always)
  const httpServer = createHttpServer(app);
  httpServer.listen(BEHIND_PROXY ? PORT : INTERNAL_PORT, '0.0.0.0', () => {
    console.log(`🔓 HTTP internal: ${BEHIND_PROXY ? PORT : INTERNAL_PORT}`);
  });

  // Create HTTPS server (if certs exist)
  const certPath = join(__dirname, '..', 'certs');
  if (existsSync(join(certPath, 'cert.pem')) && existsSync(join(certPath, 'key.pem'))) {
    const httpsOptions = {
      cert: readFileSync(join(certPath, 'cert.pem')),
      key: readFileSync(join(certPath, 'key.pem')),
      honorCipherOrder: true,
      ciphers: process.env.HTTPS_CIPHERS || 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256',
    };
    const httpsServer = createHttpsServer(httpsOptions, app);
    httpsServer.listen(BEHIND_PROXY ? INTERNAL_PORT : PORT, '0.0.0.0', () => {
      process.env.HTTPS = 'true';
      console.log(`🔒 HTTPS external: ${BEHIND_PROXY ? INTERNAL_PORT : PORT}`);
    });

    // WebSocket on HTTPS
    setupWebSocket(httpsServer);
  } else {
    // WebSocket on HTTP
    setupWebSocket(httpServer);
  }

  // Cleanup expired tokens every hour
  setInterval(cleanupExpiredTokens, 3600000);

  const proto = process.env.HTTPS ? 'https' : 'http';
  console.log(`🚀 Multi-Agent Chat ready on ${proto}://localhost:${PORT}`);
  console.log(`📡 Agents: 6 | 🔑 2FA: ready | 🛡️ E2E: ready | 🚦 Rate limit: active`);
  console.log(`🌐 OpenRouter: ${process.env.OPENROUTER_API_KEY ? '✅' : '❌'}`);
  console.log(`🔄 Behind proxy: ${BEHIND_PROXY ? 'yes' : 'no'}`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
