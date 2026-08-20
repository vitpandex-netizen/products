# JSON Output Patterns

Use these schemas for common analysis tasks.

## Stock / Trading Analysis

```json
{
  "ticker": "AAPL",
  "current_price": 198.50,
  "action": "buy|sell|hold|skip",
  "confidence": 0.85,
  "sources_checked": 3,
  "reason": "Strong earnings growth, P/E below industry average"
}
```

## Research / News Analysis

```json
{
  "topic": "AI developments 2025",
  "confidence": 0.72,
  "sources": ["techcrunch.com", "reuters.com", "arxiv.org"],
  "key_findings": [
    "New LLM benchmarks show 40% improvement",
    "Major investment in inference chips"
  ],
  "recommendation": "Monitor chip sector"
}
```

## Job / Vacancy Analysis

```json
{
  "position": "DevOps Engineer",
  "salary_range": {"min": 3000, "max": 5000},
  "skill_requirements": ["k8s", "terraform", "ci/cd"],
  "confidence": 0.91,
  "market_demand": "high"
}
```

## Classification / Routing

```json
{
  "category": "technical|financial|hr|other",
  "priority": "high|medium|low",
  "confidence": 0.88,
  "requires_human": false,
  "summary": "Urgent server outage"
}
```
