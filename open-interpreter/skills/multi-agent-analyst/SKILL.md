---
name: multi-agent-analyst
description: Parallel multi-agent analysis with structured JSON output, confidence gating, and token optimization. Use when you need to: (1) run multiple independent research/analysis/classification tasks in parallel, (2) extract structured data from unstructured sources, (3) batch-process multiple queries against shared context, (4) compare findings across sources with confidence scoring, (5) reduce output tokens via JSON-only structured responses. Do NOT use for sequential workflows, document authoring, or single-question Q&A.
---

# Multi-Agent Analyst

Run independent analysis tasks in parallel using sub-agents with shared context, structured JSON output, and confidence-based filtering.

## Core Principle: Token Economy

| Technique | Saving | How to apply |
|-----------|--------|-------------|
| JSON-only output | 50-75% output | Every agent response is pure JSON, no markdown |
| Shared context (`fork_context`) | 40-60% input | System prompt loaded once and inherited |
| Confidence gating | 20-30% | Skip low-confidence results (< 0.7) |
| Tight max_tokens | Variable | Set max_tokens = expected output size + 30% buffer |

## Workflow

```
User request
    │
    ├── Step 1: Parse request → extract task list
    │
    ├── Step 2: Spawn sub-agents in parallel (fork_context=true)
    │   └── Each: shared context + task-specific query
    │   └── Output: strict JSON with "confidence" field
    │
    ├── Step 3: Collect results
    │
    └── Step 4: Filter by confidence, merge into final answer
```

## Step-by-Step Protocol

### Step 1: Task Decomposition

Parse the user's request into parallel tasks. Each task must be **independent** — no task's output is needed by another.

**Пример:** "Проанализируй акции AAPL, проверь новости tech и найди вакансии DevOps"
→ Task A: "Analyze AAPL — price, news, recommendations"
→ Task B: "Latest tech news: AI, cloud, semiconductor"
→ Task C: "DevOps vacancies — requirements, salaries"

### Step 2: Prepare Shared Context (System Prompt)

Build a system prompt that applies to ALL tasks. Include shared data (scope, timezone, limits, rules, JSON schema).

**Must include** the JSON output schema:

```
Respond ONLY with a valid JSON object. No markdown, no code blocks, no explanations.

JSON schema:
{
  "confidence": 0.0-1.0,
  "findings": ["..."],
  "sources": ["..."],
  "recommendation": "..."
}
```

### Step 3: Spawn Sub-Agents in Parallel

Use `spawn_agent` with `fork_context: true` so all agents inherit the shared context without repeating the system prompt.

```python
for each task:
    spawn_agent(
        agent_type="worker",
        message=f"Task: {task_description}\n\nAnswer strictly as JSON.",
        fork_context=True,
        # Или укажи модель, если хочешь:
        # model="deepseek/deepseek-chat"
    )
```

**Экономия:** system prompt загружается 1 раз, 7 sub-agents не уплачивают его заново.

### Step 4: Confidence Gating

| confidence | Action |
|-----------|--------|
| ≥ 0.7 | Include in final output |
| 0.4 - 0.7 | Include with `"flagged": "low_confidence"` |
| < 0.4 | SKIP |

### Step 5: Merge Results

Combine all passing results into one structured answer.

## Token Optimization Reference

| Scenario | Without Opt | With Opt | Saving |
|----------|-----------|---------|--------|
| 5 parallel agents, 2000 tok system | 10,000 input | 2,000 input | 80% |
| Text answer vs JSON answer | ~300 tok | ~120 tok | 60% |
| Confidence filter | — | ~20% fewer results | 20% |

## Templates for Common Tasks

### Multi-Source Research

```
system: Research the following topics and return JSON for each.
        Confidence > 0.7 required.
        Schema: { "findings": [], "sources": [], "confidence": 0.0-1.0, "summary": "" }

agent_1: Task: Research latest AI developments in 2024-2025
agent_2: Task: Find recent data on semiconductor market
agent_3: Task: Analyze cloud computing trends
```

### Market / Stock Analysis

```
system: You are a financial analyst. Analyze stock data and return JSON.
        Always check at least 3 sources.
        Confidence < 0.7 → action: "skip"
        Schema: { "ticker": "", "price": 0.0, "action": "buy|sell|hold|skip", "confidence": 0.0, "reason": "" }

agent_1: Task: Analyze AAPL
agent_2: Task: Analyze MSFT
agent_3: Task: Analyze GOOGL
```

## Cost Report Template

At the end, collect all agent results into one report:

```json
{
  "tasks_total": 5,
  "tasks_completed": 4,
  "tasks_skipped": 1,
  "avg_confidence": 0.82,
  "results": [ ... ],
  "summary": "3 strong signals, 1 with caveats, 1 skipped"
}
```
