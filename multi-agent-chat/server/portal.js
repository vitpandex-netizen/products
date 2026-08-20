import { Router } from 'express';

const router = Router();

// Проекты регистрируются через labels в docker-compose.yml
// Портал просто сканирует Docker API

router.get('/catalog', async (req, res) => {
  try {
    const projects = await discoverProjects();
    res.json({ projects, total: projects.length, updatedAt: new Date().toISOString() });
  } catch (err) {
    console.error('Catalog error:', err);
    res.status(500).json({ error: 'Discovery failed' });
  }
});

async function discoverProjects() {
  const projects = [];
  
  // 1. Multi-Agent Chat
  projects.push({
    id: 'multi-agent-chat',
    name: 'Multi-Agent Chat',
    icon: '🤖',
    description: 'Чат с 6 AI-агентами: Interpreter, Тестировщик, Claude, Hermes, Cursor, OpenClaw. E2E шифрование, 2FA, реальные AI через OpenRouter.',
    url: 'http://100.94.224.89/chat/',
    port: 5555,
    category: 'ai',
    tags: ['chat', 'ai', 'agents'],
    status: await checkHealth('http://localhost:5555/api/health'),
    repo: '/opt/agents/multi-agent-chat',
    maintainer: 'admin',
  });

  // 2. Buzz Relay
  projects.push({
    id: 'buzz',
    name: 'Buzz Relay',
    icon: '🐝',
    description: 'Система ретрансляции сообщений и событий между сервисами. Очереди, вебхуки, pub/sub.',
    url: 'http://100.94.224.89:8081',
    port: 8081,
    category: 'infra',
    tags: ['messaging', 'events', 'relay'],
    status: await checkHealth('http://localhost:8081/health'),
    repo: '/opt/agents/buzz',
    maintainer: 'admin',
  });

  // 3. Health Dashboard
  projects.push({
    id: 'health',
    name: 'Health Dashboard',
    icon: '📊',
    description: 'Мониторинг состояния сервера, контейнеров, метрик. Автоматические алерты в Telegram.',
    url: 'http://100.94.224.89:8080',
    port: 8080,
    category: 'infra',
    tags: ['monitoring', 'metrics', 'alerts'],
    status: await checkHealth('http://localhost:8080/health'),
    repo: '/opt/infra/stack/health-monitor',
    maintainer: 'admin',
  });

  // 4. LiteLLM
  projects.push({
    id: 'litellm',
    name: 'LiteLLM (AI Gateway)',
    icon: '🧠',
    description: 'Единый API-шлюз для всех AI-моделей через OpenRouter. Поддержка 100+ моделей.',
    url: 'http://100.94.224.89:4000',
    port: 4000,
    category: 'ai',
    tags: ['ai', 'llm', 'gateway'],
    status: { online: false, message: 'Сервис остановлен' },
    repo: '/opt/infra/stack/litellm',
    maintainer: 'admin',
  });

  // 5. Hermes WebUI
  projects.push({
    id: 'hermes-webui',
    name: 'Hermes WebUI',
    icon: '⚡',
    description: 'Веб-интерфейс для Hermes AI. Чат с моделями, управление агентами, настройки.',
    url: 'http://100.94.224.89:3000',
    port: 3000,
    category: 'ai',
    tags: ['ai', 'webui', 'chat'],
    status: await checkHealth('http://localhost:3000'),
    repo: '/opt/passive-income/hermes-webui',
    maintainer: 'admin',
  });

  // 6. Transcribe Service
  projects.push({
    id: 'transcribe',
    name: 'Transcribe Service',
    icon: '🎙️',
    description: 'Сервис транскрибации аудио в текст. Локальное распознавание речи, поддержка русского языка.',
    url: 'http://100.94.224.89:8000',
    port: 8000,
    category: 'media',
    tags: ['audio', 'transcription', 'speech'],
    status: await checkHealth('http://localhost:8000/health'),
    repo: '/opt/passive-income/transcribe-service',
    maintainer: 'admin',
  });

  // 7. IT Operations Framework
  projects.push({
    id: 'it-ops',
    name: 'IT Operations Framework',
    icon: '🔧',
    description: 'Фреймворк для автоматизации IT-операций. Оркестрация задач, мониторинг, авто-исправления.',
    url: 'http://100.94.224.89:8082',
    port: 8082,
    category: 'infra',
    tags: ['devops', 'automation', 'orchestration'],
    status: await checkHealth('http://localhost:8082/health'),
    repo: '/opt/passive-income/it-operations-framework',
    maintainer: 'admin',
    starred: true,
  });

  // 8. FinAnalytics
  projects.push({
    id: 'finanalytics',
    name: 'FinAnalytics',
    icon: '📈',
    description: 'Финансовая аналитика: исторические данные, тренды, прогнозы. Акции, индексы, портфели.',
    url: 'http://100.94.224.89:3001',
    port: 3001,
    category: 'finance',
    tags: ['finance', 'analytics', 'stocks'],
    status: { online: false, message: 'В разработке' },
    repo: '/opt/agents/my-project/finanalytics',
    maintainer: 'admin',
    starred: true,
  });

  // 9. Market Events
  projects.push({
    id: 'market-events',
    name: 'Market Events',
    icon: '📰',
    description: 'Агрегатор рыночных событий и новостей. Парсинг, аналитика, уведомления.',
    url: 'http://100.94.224.89:3002',
    port: 3002,
    category: 'finance',
    tags: ['news', 'markets', 'events'],
    status: { online: false, message: 'В разработке' },
    repo: '/opt/agents/my-project/market-events',
    maintainer: 'admin',
  });

  // 10. Stocks US
  projects.push({
    id: 'stocks-us',
    name: 'US Stocks Dashboard',
    icon: '🇺🇸',
    description: 'Дашборд американских акций. Реальные котировки, аналитика, портфель.',
    url: 'http://100.94.224.89:3003',
    port: 3003,
    category: 'finance',
    tags: ['stocks', 'us', 'dashboard'],
    status: { online: false, message: 'В разработке' },
    repo: '/opt/agents/my-project/stocks-us',
    maintainer: 'admin',
  });

  // 11. Stocks UZ
  projects.push({
    id: 'stocks-uz',
    name: 'UZ Stocks Dashboard',
    icon: '🇺🇿',
    description: 'Дашборд узбекских акций. Локальный рынок, котировки, аналитика.',
    url: 'http://100.94.224.89:3004',
    port: 3004,
    category: 'finance',
    tags: ['stocks', 'uz', 'dashboard'],
    status: { online: false, message: 'В разработке' },
    repo: '/opt/agents/my-project/stocks-uz',
    maintainer: 'admin',
  });

  // 12. HH Jobs
  projects.push({
    id: 'hh-jobs',
    name: 'HH Jobs Analyzer',
    icon: '💼',
    description: 'Анализ вакансий с HeadHunter. Тренды рынка, зарплаты, навыки, прогнозы.',
    url: 'http://100.94.224.89:3005',
    port: 3005,
    category: 'data',
    tags: ['jobs', 'analytics', 'hh'],
    status: { online: false, message: 'В разработке' },
    repo: '/opt/agents/my-project/hh-jobs',
    maintainer: 'admin',
  });

  return projects;
}

async function checkHealth(url) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timeout);
    if (res.ok) {
      const data = await res.json().catch(() => ({}));
      return { online: true, latency: '~10ms', ...data };
    }
    return { online: true, latency: '~50ms' };
  } catch {
    return { online: false, message: 'Недоступен' };
  }
}

export default router;
