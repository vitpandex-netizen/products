# Enterprise Agentic Protocol: Spec-First TDD & Multi-Agent Governance

> Industrial-grade development protocol extracted from 15 video materials (600+ hrs enterprise pipeline experience).

---

## Core Principle

**No code without contract. No contract without interview. No merge without red-team audit.**

Every task follows strict 5-stage pipeline:
```
[INTERVIEW] -> [SPECIFICATION] -> [FAIL-TESTS / RED] -> [CODE-TO-GREEN] -> [RED-TEAM AUDIT]
```

---

## 1. Methodology: Spec & TDD Pipeline

### Interview Protocol
- **Forbidden**: generating code from raw request
- **Required**: 3-5 critical clarifying questions on architecture, loads, edge cases
- **Output**: Technical contract — I/O formats, error codes, SLA/timeouts, auth, rate limits

### TDD-Lock (Test-First Contract)
- Tests written **before** any implementation code
- Tests must capture: auth, rate limits, error codes, boundary conditions
- **Mandatory**: run tests, confirm RED (fail), then iterate code until GREEN
- **Zero tolerance**: "all works" without test run log = critical error

### Three Karpathy Layers
1. **Spec** — Technical specification (ТЗ)
2. **Verify** — Independent verification (tests, audits, red-team)
3. **Environment** — Pinned rules, skills, MCP servers, configs

---

## 2. Tooling & Data Ingestion

### Agent Reach / CLI Scrapers
- Extract live context from GitHub, Reddit, YouTube, X
- Bypass rate limits and paid APIs
- Feed fresh data into specification & test generation

### Everything Claude Code (ECC) Scale
- Dozens of specialized subagents, hooks, MCP servers
- Parallel execution in isolated contexts

### UI Standards (Apple HIG)
- No template UI
- Instant touch feedback (<=16ms)
- Physics-based animations, no micro-freezes

---

## 3. Risk Audit Matrix

| Risk Vector | Source | Damage | Mitigation |
|-------------|--------|--------|------------|
| Silent Hallucination & Self-Validation | Tests written after code | Tests pass but code broken in prod | **TDD-Lock**: no logic without pre-committed failing tests |
| Context Bloat & Token Waste | Monolithic agent execution | Context loss at 20-30 steps, cost explosion | Orchestrator decomposes; workers spawn fresh in worktrees |
| Supply Chain & CLI Execution | Unverified MCP plugins/scripts | Unauthorized FS access, env compromise | Docker containers for workers, read-only scrapers, secret masking |
| Merge Conflict Hell | Parallel agents in one branch | Codebase corruption | **Git Worktree isolation** per subtask; merge only via PR with review |

---

## 4. Action Plan

### Step 1: Git Worktree Infrastructure
```bash
# Setup script: setup_worktree.sh
# Usage: setup_worktree.sh <task-id> <base-branch>
git worktree add .worktrees/task-<N> <base-branch>
```
- Isolated working tree per subtask
- No conflicts with main branch
- Cleanup on merge

### Step 2: System Prompt Integration
- Embed protocol into: CLAUDE.md, .cursorrules, agent system prompts
- Enforce at configuration level

---

## 5. Workflow Constraints (Execution Algorithm)

### Stage 1: Interview & Specification
- If request lacks exhaustive description -> STOP
- Ask 3-5 critical questions
- Produce technical contract

### Stage 2: Pre-Code Testing (RED Phase)
- Write tests (Unit/E2E/Integration) from Spec
- **Must FAIL** — no implementation code exists yet
- Commit failing tests

### Stage 3: Implementation (GREEN Phase)
- Write minimal code to pass tests
- Loop: Fix -> Test -> Analyze trace -> Fix
- **Completion**: 100% tests pass, >=80% coverage
- **Required**: provide test run output log

### Stage 4: Security Audit & Verification
- Secret leaks & hardcoded configs check
- UI standards: instant feedback, no animation jank
- Input validation at all boundaries
- Negative scenarios: SQLi, XSS, race conditions, rate limit bypass, memory exhaustion
- Every found vector -> test coverage required before close

---

## 6. Zero-Tolerance Rules (Non-Negotiable)

1. **NO VIBE CODING** — no code from guesses without spec + tests
2. **NO FAKE REPORTING** — "done and works" without test runtime log = critical error
3. **NO TESTS AFTER CODE** — test-first only
4. **NO MONOLITHIC CONTEXT** — complex epics -> isolated micro-tasks in worktrees

---

## 7. Practical Checklists

### Pre-Implementation Checklist
- [ ] Interview conducted (3-5 questions answered)
- [ ] Spec written: I/O formats, errors, SLA, auth, rate limits
- [ ] Tests written covering spec + edge cases
- [ ] Tests committed and confirmed RED
- [ ] Git worktree created for this task

### Implementation Checklist
- [ ] Code passes all tests (GREEN)
- [ ] Coverage >=80%
- [ ] Test run log attached
- [ ] No secrets in code
- [ ] UI feedback <=16ms, no jank

### Pre-Merge Audit Checklist
- [ ] Static analysis clean
- [ ] Negative scenarios tested (SQLi, XSS, race, rate-limit, OOM)
- [ ] Each attack vector has test coverage
- [ ] PR opened from worktree
- [ ] Independent review passed

---

## 8. Integration Points

- **Git Worktrees**: `.worktrees/task-<N>` per subtask
- **Message Bus**: `:8200` for cross-agent coordination
- **Change Log**: `:8310` for audit trail
- **Context DB**: `:8006` for shared knowledge
- **Skills**: This protocol loads via `skill_view(enterprise-agentic-protocol)`
