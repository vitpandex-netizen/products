export const AGENTS = [
  {
    id: 'interpreter',
    name: 'Interpreter',
    emoji: '🧠',
    color: '#6366f1',
    role: 'Координатор, отвечает на общие вопросы, подводит итоги.'
  },
  {
    id: 'tester',
    name: 'Тестировщик',
    emoji: '🔍',
    color: '#f59e0b',
    role: 'QA-инженер: баги, тест-кейсы, качество кода.'
  },
  {
    id: 'claude',
    name: 'Claude',
    emoji: '🤖',
    color: '#d97706',
    role: 'Архитектор: рефакторинг, best practices, дизайн системы.'
  },
  {
    id: 'hermes',
    name: 'Hermes',
    emoji: '⚡',
    color: '#8b5cf6',
    role: 'Оптимизатор: производительность, CI/CD, DevOps, метрики.'
  },
  {
    id: 'cursor',
    name: 'Cursor',
    emoji: '🖱️',
    color: '#06b6d4',
    role: 'Code-reviewer: ревью кода, тесты, автодополнение.'
  },
  {
    id: 'openclaw',
    name: 'OpenClaw',
    emoji: '🦞',
    color: '#ec4899',
    role: 'Security/Data: безопасность, данные, мониторинг, дашборды.'
  }
];

export function getAgent(id) {
  return AGENTS.find(a => a.id === id);
}

export function getAgentIds() {
  return AGENTS.map(a => a.id);
}
