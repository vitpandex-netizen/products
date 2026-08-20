import fetch from 'node-fetch';
import { AGENTS, getAgent, getAgentIds } from './prompts.js';

const OPENROUTER_API = 'https://openrouter.ai/api/v1/chat/completions';

// Дешёвая, но умная модель — 1 вызов на всех агентов
const BATCH_MODEL = 'openai/gpt-4o-mini'; // $0.15/1M input, $0.60/1M output
const FALLBACK_MODEL = 'deepseek/deepseek-chat'; // ещё дешевле

export async function callAllAgents(messages, context, apiKey) {
  const agentDefs = AGENTS.map(a => `"${a.id}": ${a.emoji} ${a.name} — ${a.role}`).join('\n');

  const systemPrompt = `Ты — диспетчер multi-agent чата. Пользователь пишет сообщение, а ты должен ответить ОТ ЛИЦА КАЖДОГО из 6 агентов.

Агенты:
${agentDefs}

Правила:
1. Ответь строго в формате JSON: { "agent_id": "ответ агента" }
2. Ключи — id агентов (interpreter, tester, claude, hermes, cursor, openclaw)
3. Каждый ответ — 1-3 предложения от лица агента, в его стиле
4. Interpreter — главный, отвечает первым и самым развёрнутым
5. Остальные — по их специализации
6. Отвечай на том же языке, что и пользователь
7. Если вопрос не по теме агента — он может кратко сказать "пропускаю"`;

  const userMsg = context
    ? `Контекст чата: ${context}\n\nПоследнее сообщение: ${messages[messages.length - 1]?.text || ''}`
    : messages[messages.length - 1]?.text || '';

  if (!apiKey) {
    return fallbackAll(messages);
  }

  const body = {
    model: BATCH_MODEL,
    messages: [
      { role: 'system', content: systemPrompt },
      ...messages.slice(-10).map(m => ({
        role: m.sender_role === 'agent' ? 'assistant' : 'user',
        content: `${m.sender_name}: ${m.text}`
      })),
      { role: 'user', content: userMsg }
    ],
    max_tokens: 2048,
    temperature: 0.7,
    response_format: { type: 'json_object' },
  };

  try {
    const res = await fetch(OPENROUTER_API, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:5555',
        'X-Title': 'Multi-Agent Chat',
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30000),
    });

    if (!res.ok) {
      const errText = await res.text();
      console.error(`[batch] API error ${res.status}:`, errText.slice(0, 200));
      return fallbackAll(messages);
    }

    const data = await res.json();
    const content = data.choices?.[0]?.message?.content;
    if (!content) return fallbackAll(messages);

    try {
      const parsed = JSON.parse(content);
      const result = {};
      for (const agent of AGENTS) {
        result[agent.id] = parsed[agent.id] || fallbackOne(agent.id, messages);
      }
      return result;
    } catch {
      console.error('[batch] JSON parse error, raw:', content.slice(0, 100));
      return fallbackAll(messages);
    }
  } catch (err) {
    console.error('[batch] Error:', err.message);
    return fallbackAll(messages);
  }
}

// ======== FALLBACKS (без API) ========
function fallbackOne(agentId, messages) {
  const lastMsg = messages[messages.length - 1]?.text?.toLowerCase() || '';
  const agent = getAgent(agentId);
  const name = agent?.name || agentId;

  const patterns = {
    interpreter: [
      { match: ['привет', 'здравствуй', 'хай'], reply: `👋 Привет! Я ${name}. Чем могу помочь?` },
      { match: ['пока', 'до свидания'], reply: `👋 До связи!` },
      { match: ['спасибо', 'благодарю'], reply: `🙌 Пожалуйста!` },
    ],
    tester: [
      { match: ['тест', 'баг', 'ошибка'], reply: `🔍 **${name}**: Анализирую. Нужно проверить граничные случаи и написать тесты.` },
    ],
    claude: [
      { match: ['архитектур', 'дизайн', 'структур', 'паттерн'], reply: `🤖 **${name}**: Архитектура разумная. Рекомендую композицию.` },
    ],
    hermes: [
      { match: ['оптимизац', 'скорость', 'производительность', 'билд'], reply: `⚡ **${name}**: Можно сократить время сборки на 30%.` },
    ],
    cursor: [
      { match: ['код', 'напиши', 'функция', 'реализаци'], reply: `🖱️ **${name}**: Вот оптимальная реализация.` },
    ],
    openclaw: [
      { match: ['данные', 'лог', 'метрик', 'мониторинг', 'безопаснос'], reply: `🦞 **${name}**: Анализ завершён. Аномалий нет.` },
    ],
  };

  const agentPatterns = patterns[agentId] || [];
  for (const p of agentPatterns) {
    if (p.match.some(m => lastMsg.includes(m))) return p.reply;
  }
  return '';
}

function fallbackAll(messages) {
  const result = {};
  for (const agent of AGENTS) {
    result[agent.id] = fallbackOne(agent.id, messages);
  }
  // Ensure interpreter always has something
  if (!result.interpreter) {
    const lastMsg = messages[messages.length - 1]?.text || '';
    result.interpreter = `🧠 **Interpreter**: Получил твой запрос. ${lastMsg ? 'Думаю над ответом...' : 'Чем могу помочь?'}`;
  }
  return result;
}

export { AGENTS, getAgent, getAgentIds } from './prompts.js';
