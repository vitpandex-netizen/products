## User Profile

The user works on macOS with zsh and uses Interpreter as a serious day-to-day automation tool, often in Russian. They care about durable setup, 24/7 automation, externalized memory, and low-friction continuation across sessions. Their recurring technical footprint includes /Volumes/External as the main storage/work area, Oracle/Tailscale as lightweight always-on infrastructure, OpenRouter/DeepSeek as the primary model path, local Ollama as fallback, and Telegram forum topics / launchd / pm2 as everyday operational surfaces. They repeatedly work across project unification, AI/agent infrastructure, passive-income automation, secure secret handling, Telegram/mobile access, local-market research, and office-style deliverables.

They prefer agents that keep going once the direction is clear, but without hallucinating progress or facts. They often ask for concrete artifacts: working infra, pushed code, real .docx files, reconciled spreadsheets, automated scripts, monitoring topics, or ready-to-forward Telegram text. They also care about multimodal capability growth: screenshots/images, voice, diagrams, PDF/Word/Excel handling, and Telegram/mobile access that actually works, not just scaffolding.

Stable constraints and habits observed in recent memory: external-drive-first storage is important; internal disk should stay free for swap, except small reliability-critical scripts that should run locally rather than from an external drive; free options should be considered first; new hosted services should be optional and justified by a serious real need; secrets should live in protected encrypted storage; prior user artifacts should be treated as primary evidence when refining a workflow or analysis; and repetitive progress narration is unwelcome compared with finished milestones plus verification.

## User preferences

- Respond in Russian when the user is speaking Russian.
- Default to free options first when they exist; the user explicitly said: ты старайся мне предлогать бесплатные варианты в начале.
- For model/provider choices, treat cost control as an active default: cheap practical models first, expensive reasoning only where clearly needed, and remove premium profiles quickly if spend spikes.
- Treat Oracle as a small 24/7 runtime host, not just a VPN node, when the user frames it as a place to run projects all the time.
- Keep going after short confirmations like Continue, давай, or готово?; do not over-request confirmation once the direction is clear.
- Be autonomous, but honor the user wording: не фантазировать и спрашивать, но при этом быть максимально автономным.
- Prefer finished milestones, verification, and concrete outputs over progress spam; the user repeatedly asks что в итоге? and покажи мне результат.
- If the user says something started after yesterday settings, inspect recent launch agents, startup jobs, and config changes first instead of starting with generic theory.
- When the user selects or states an exact schedule like Расписание: 09:00 и 21:00 (Ташкент), implement that schedule literally and verify it afterward.
- When the user asks готово?, answer with a concrete completion check, not a vague status update.
- When the user asks whether sessions can be remembered after closing and agrees with да давай, default to saving a short continuity note and offering a reminder/continue from here flow on next start, while staying honest that full dialog restoration is not available.
- When the user asks "я могу с тобой общатся с мобильника?" or pushes Telegram access, treat it as a practical remote-chat channel request and try to reuse existing Telegram setup before proposing a fresh manual flow.
- When the user pastes a token or says to look at how it was done in Claude/cloud, finish the Telegram setup end-to-end and inspect the existing project convention first.
- When the user treats a document/TZ as execution and says "это ТЗ для тебя, нужно чтобы ты сделал готовое техническое решение", default to building the working solution, not stopping at a spec.
- On this Mac, container tasks should assume Orbstack first when the user says "мы работаем не через docker а через orbstack"; check the Orbstack socket/context before generic Docker debugging.
- When the user pastes the exact error text or sends a screenshot and asks what happened, analyze the concrete evidence first and avoid unnecessary restarts or redesign unless they ask for a fix.
- For Telegram bot wording/routing tasks, make the bot identity explicit and keep topic boundaries strict; if the user asks for a separate AI topic or private-chat flow, treat that as an isolation/routing request, not just cosmetic text editing.
- If the user says "ты этот сбился немнож ко. Давай, нач нем сначала.", treat the prior attempt as stale, restart cleanly, and re-establish scope before more edits/actions.
- Keep topic boundaries strict across projects and Telegram threads; when the user says variants of "не путай топики" or reports cross-posting, audit the whole related automation set and then report what was fixed.
- Treat user-specified schedules as defaults to implement literally until changed; keep the settled matrix in memory so later schedule edits start from the saved baseline instead of rediscovery.
- When the user asks "а что за batch processor это что?" or questions a scheduled job, explain what it is plainly and disable obsolete/duplicate automation when appropriate instead of defending it.
- When the user asks "что происходит?" during an interrupted/background run, answer with a short state summary first: what is already done, what is still missing, and whether anything is still running.
- Default secrets to encrypted protected storage. The user explicitly said variants of все ключи надо хранить в защищеном месте и с шифрованием and все ключи и пароли хранить только в хранилище по всем проектам.
- Do not rely on macOS Keychain as the only secret store for critical project workflows when the user has already seen Keychain-not-saving behavior from the sandbox.
- For passive-income/automation work, default toward scheduled autonomous research, continuous improvement, and community-source monitoring instead of reports only.
- Start cross-project infra tasks with a broad audit/unification pass when the user asks to изучил все проекты... и сделай какюу то унификация.
- Keep git-based workflow as the default for repo work; the user said не забывай все черз гет как положено делать.
- If Tailscale access already exists, check it first and avoid re-asking for basic server access details.
- When the user says to inspect everything on the machine, inspect the real filesystem/runtime state broadly before narrowing; do not just check one guessed path.
- When the user asks what a new service is for and says "я не знаю для чего они нужны и как они могут нам помочь" -> explain the concrete usefulness first, not just what the brand is.
- Treat Supabase, Vercel, and similar hosted services as optional; per the user’s correction, connect them only when "есть прям серьезная необходимость".
- For constrained servers, follow the user’s steer "ресурсов очень мало поэтому тогда граф интерфейс не стоит" -> prefer Telegram/CLI monitoring over GUI/RDP.
- For monitoring work, use a dedicated forum topic when the user says "сделай отдельно топик мониторинг".
- For monitoring behavior, default to "если все ок, можно не сообщать" plus sustained-failure alerting instead of healthy-state spam.
- For hardware/local-market shopping tasks, if the user says "изучи этот момент по макисмум", do full cause analysis + local-market scan + concrete shortlist, not a quick take.
- For Tashkent shopping comparisons, include price/quality/speed plus TCO, endurance, and normalized cost metrics when the user asks for "цена качество скорость" and "цена за 1мб".
- For local listings, carry the user’s stale-stock warning forward: "обьявление старое не факт что он есть в наличии" -> advise confirming availability with the seller.
- When the user asks for Telegram-format output, provide a ready-to-forward message, but do not imply real sending unless a live Telegram path is already verified.
- For broad app-capability questions like "What settings can you change in this app?", answer with a categorized inventory rather than a yes/no.

## General Tips

- The most reliable first pass on this workstation is usually: check recent memory/session notes, then inspect the real filesystem/runtime state, then change configuration.
- Prefer exact user wording, exact file paths, exact thread IDs, and exact error strings in durable notes; these are strong retrieval handles for future runs.
- External-drive-first is the standing storage pattern, but small launchd/runtime-critical scripts may need to live on the internal disk for reliability.
- When changing launchd, pm2, cron, or bot/runtime behavior, verify with the real status command/log/API response before calling it done.
- For Oracle work on the small VM, keep solutions lightweight; avoid GUI-heavy paths and avoid forcing unnecessary platform complexity.
- For Telegram/bot flows, distinguish clearly between scaffolding prepared, service live now, and reboot-persistent startup configured.
- For settings/config inspection, avoid copying raw secret-bearing dumps into answers or memory; summarize categories and redact values.
- For hardware/market research, keep a bright line between verified facts, user-confirmed tests, and provisional market assumptions.
- When a user interrupt arrives mid-run, summarize state first before continuing exploration.
- For remote-server edits that involve stateful monitoring, prefer persistent state files/volumes so behavior survives restarts.

## What's in Memory

### /Users/vitaliyr/Downloads and interpreter runtime

#### 2026-08-08

- launchd failover scheduling, freeze diagnosis, and session persistence: com.interpreter.failover, StartCalendarInterval, /tmp/.interpreter_network_state, session_startup.py, /Volumes/External/interpreter/memories/sessions
  - desc: Covers diagnosing the recent Mac freeze after settings changes, identifying the 60-second failover launchd job as the culprit, redesigning it for 09:00/21:00 Tashkent, and adding continuity summaries so future sessions can remind the user what was happening. Search this first when the user reports slowdowns/freezes after config changes or asks whether Interpreter can remember and resume work.
  - learnings: Check recent session summaries and launch agents first. The validated fix moved runtime-critical failover pieces local, replaced StartInterval with calendar triggers, and paired it with a short saved-summary continuation flow.

- restart-after-interruption and status-first recovery: ты этот сбился немнож ко. Давай, нач нем сначала., <turn_aborted>, что происходит, stale partial plan
  - desc: Covers the user's explicit clean-restart preference when a run drifts, plus the status-summary expectation during interrupted/background bot work. Search this first when a prior attempt was aborted or when background execs may still be running in cwd=/Users/vitaliyr/Downloads or the Interpreter Telegram/mobile workflow.
  - learnings: Treat aborted background state as stale until re-checked, do not continue a drifting plan after a restart-style correction, and answer with a concise done/missing/running summary before more exploration when the user asks what is happening.

- Oracle VM Telegram monitoring and sustained alerts: health-monitor, createForumTopic, message_thread_id 203, 409 Conflict, /opt/infra/stack/health-monitor/monitor.py, state.json
  - desc: Covers explaining the old `✅ All agents healthy` message, redesigning alerts to fire only after sustained failures, creating the `📊 Мониторинг` forum topic in `AI Assistant — Family`, and integrating Oracle monitoring/bot flows there. Search this for Oracle monitoring, alert-policy tuning, forum-topic routing, or Telegram-based server ops on the small VM.
  - learnings: Healthy checks should stay silent; the validated policy is 4 consecutive 15-minute failures, recovery alerts, and 24-hour re-alerting. Topic creation succeeded with `message_thread_id 203`, while polling verification remained partial because of a Telegram `409 Conflict` that points to competing pollers/webhooks.

- product/service adoption thresholds and Interpreter settings inventory: supabase, vercel, serious necessity, interpreter-app config get, agentAccess, config list unsupported
  - desc: Covers two lightweight but recurring decision areas: how to frame optional hosted services like Supabase/Vercel against the existing Oracle VM, and how to enumerate changeable Interpreter settings from live config. Search this for “what is this service for?”, “should we connect it?”, or “what can this app change?”.
  - learnings: New hosted services should be framed as optional and only introduced on clear need. In this runtime, `interpreter-app config get` is the reliable CLI path; `config list` is unsupported, and raw config output may expose secrets if copied carelessly.

- Telegram/mobile bot live setup: InterP_Ai_bot, .token, python-telegram-bot-22.8, pm2, getMe, queries.jsonl
  - desc: Covers the live Telegram bot setup for chatting from mobile, including token-file path, venv workaround for externally-managed Python, getMe verification, pm2 runtime, and interruption-status handling. Search this for Telegram/mobile access, bot activation state, or live-vs-scaffolded bot questions.
  - learnings: Preserve the distinction between framework ready and service live. The newer rollout ended with the bot running under pm2 and verified via getMe, but startup-on-boot still depended on a separate sudo-gated step.

- USB4 NVMe heat diagnosis and Tashkent SSD shortlist: Ugreen CM850, Samsung PM981a, 49°C, OLX.uz, Kingston NV2 2TB, Team G50 2TB
  - desc: Covers diagnosing enclosure heat in a USB4 NVMe case, deciding whether the current SSD needs replacement, comparing 1 TB vs 2 TB options on the Tashkent market, and preparing a Telegram-ready handoff. Search this for external SSD heat worries, Tashkent storage shopping, or TCO-oriented hardware comparisons.
  - learnings: The highest-signal test was removing the silicone sleeve and re-checking temperature; `49°C` shifted the conclusion from emergency replacement to optional upgrade. Market listings need freshness caveats because stale ads were a user-raised issue.

- Tashkent AI server research plus Word/spreadsheet reconciliation: RTX 4090, RTX A5000, Mac Mini M4 Pro, Vast.ai, ai-server-cto-package.docx, ai_server_comparison (7) (1).xlsx
  - desc: Covers CTO/investor-style AI server analysis for Tashkent, monetization-vs-personal-use framing, actual .docx deliverable creation, and comparison against the user’s earlier spreadsheet. Search this first for hardware recommendation follow-ups, monetization framing, Word-export workflow, or prior-art reconciliation.
  - learnings: Separate verified listings from inference, use local B2B rental as the main monetization frame rather than passive Vast.ai assumptions, validate .docx directly instead of relying on PDF conversion, and treat the earlier spreadsheet corrections as higher-trust evidence.

#### 2026-08-07

- macOS permissions and image-question handling: cuadriver, Accessibility, Screen Recording, это ты?, image question
  - desc: Covers separate required vs optional macOS permissions for computer-use/image tasks and the rule to answer direct image-identity questions honestly; use when desktop permissions or screenshot/image truthfulness is at issue. Applies to cwd=/Users/vitaliyr/Downloads and interpreter runtime behavior.
  - learnings: Keep permission requests scoped to the actual tool path, and answer direct image-identification questions without overclaiming.

### /Volumes/External/dev/my-project and Oracle runtime

#### 2026-08-08

- passive-income infra hardening, project memory, and continuous-improvement rules: passive-income, PROJECT_MEMORY.md, graphify, launchd, Oracle cron, sync-all, .env permissions
  - desc: Covers the broader passive-income system hardening pass: ecosystem discovery across Hermes/Claude state, MVP + Telegram topic delivery, launchd/Oracle redundancy, migration scripts, security fixes, and in-repo persistent project memory. Search this when the user asks to understand everything being done, unify ownership, or continue hardening the passive-income system with durable memory.
  - learnings: Keep `/Volumes/External/dev/` as source of truth, mirror to Oracle for 24/7, maintain `PROJECT_MEMORY.md`, and treat continuous improvement plus idea/community monitoring as standing project rules. Graphify is available but should be used when architectural mapping is truly helpful, not automatically.

#### 2026-08-07

- passive-income recovery, vault, and autonomous research: passive-income, Oracle Cloud, Tailscale exit node, vault.py, auto_trigger(min_score=45), thread_id=127
  - desc: Covers restoring Oracle/Tailscale access after disk disruption, rebuilding secrets into a vault, repairing DB/runtime continuity, and resuming scheduled research plus prototypes. Search this for passive-income recovery, vault-backed config, Telegram topic 127 delivery, or Oracle/Tailscale host continuity.
  - learnings: Confirm Tailscale and the real downloaded key first, keep code reading vault indirection rather than raw env secrets, and verify recovery with a fresh research artifact plus real schedule checks before declaring the system restored.

### /Volumes/External/dev/my-project shared LLM routing + Interpreter cost control

#### 2026-08-08

- passive-income cleanup, launchd schedule matrix, and cheap routing defaults: passive-income/src/db.py, sqlite3.OperationalError: unable to open database file, batch-processor, shared/llm.py, Ling-2.6-flash, qwen/qwen3.7-flash, 15/15 проверок пройдено
  - desc: Covers strict project/topic separation inside my-project, the passive-income SQLite fix, normalized launchd/runner schedules for passive-income/stocks/hh-jobs/failover/watchdog, and the cheap-first LLM routing stack. Search this first for passive-income runtime issues, schedule edits, cross-project leakage, or model-routing changes in cwd=/Volumes/External/dev/my-project with related Interpreter config.
  - learnings: The saved schedule matrix is the durable baseline; batch-processor is legacy and was disabled; fix unable to open database file with a persistent SQLite connection; keep the final chain Ling -> DeepSeek V4 Flash -> Ollama only without network; and verify real modelId plus end-to-end imports/tests after routing edits.

### /Volumes/External/dev Oracle/Tailscale unified infra

#### 2026-08-07

- unified 24/7 Oracle infra for multiple projects: Caddy, nginx, stocks-uz, stocks-us, hh-jobs, watchdog, launchd, cron
  - desc: Covers consolidating several agent projects onto the small Oracle VM with reverse proxy, scheduling, shared router, and weekend guards. Search this when tasks touch multi-project Oracle hosting, service consolidation, or scheduler sanity across projects.
  - learnings: Stop nginx before binding Caddy to port 80, normalize paths to the actual `my-project` nesting, and avoid forcing LiteLLM + PostgreSQL-shaped complexity onto a ~1 GB Oracle host.

### /Volumes/External workstation + model failover

#### 2026-08-07

- external disk rebuild and failover routing: diskutil eraseDisk APFS External disk4, /Volumes/External, OLLAMA_MODELS, qwen3:1.7b, DeepSeek V4 Flash via OpenRouter, failover.sh
  - desc: Covers restoring the external APFS disk, cloning repos via SSH, reorganizing workstation projects into themed folders, moving Ollama models onto the external disk, and wiring DeepSeek/OpenRouter primary with Ollama fallback. Search this for workstation rebuild, external-drive-first layout, Ollama on external storage, or failover questions.
  - learnings: Preserve data before destructive disk actions, inventory the real workstation before reorganizing it, use qwen3:1.7b-class fallback models for M1 Air 8GB, and keep provider wording explicit so internal config aliases do not confuse future sessions.

### /Volumes/External/interpreter multimodal memory and startup

#### 2026-08-07

- multimodal memory, startup intelligence, and Telegram/mobile access scaffolding: /Volumes/External/interpreter/memories, session_startup.py, image-reader, telegram-bot, NO TOKEN IN KEYCHAIN
  - desc: Covers external-drive persistent memory, caching, startup scripts, multimodal capability scaffolding (images, voice, diagrams, office/file tools), earlier Keychain-backed Telegram preparation, and the later live Telegram bot path. Search this for memory persistence, startup automation, multimodal capability routing, or old Telegram scaffolding assumptions.
  - learnings: Preserve the distinction between framework ready and service live. Earlier memory ended at `NO TOKEN IN KEYCHAIN`; newer memory adds a working pm2-run bot but still keeps the reboot-persistence caveat separate.

### Older Memory Topics

#### /Users/vitaliyr/Downloads and interpreter runtime

- prompt placeholder bug and memory hygiene: [PERSON_NAME], placeholder bug, environment-level blocker, prompt injection
  - desc: Covers the environment-level placeholder issue and why it should be treated as a system/runtime blocker rather than cosmetic text cleanup. Applies to cwd=/Users/vitaliyr/Downloads and interpreter prompt/runtime debugging.

#### /Volumes/External/dev and model-routing workflows

- OpenRouter guardrails and blocked requests diagnosis: openrouter, blocked requests, no_biscuit_no_service, guardrail, diagnosis
  - desc: Covers diagnosing OpenRouter-side request blocking/guardrail behavior and preserving exact error strings for routing. Use when API requests are being refused or filtered and the user wants root-cause analysis.

- multi-agent analyst skill and custom-instructions routing: multi-agent analyst, openrouter routing, custom instructions, skill behavior
  - desc: Covers the earlier multi-agent analyst/openrouter/custom-instructions work and should be searched when task orchestration or model-routing behavior needs continuity with prior setup decisions. Applies to cwd under /Volumes/External/dev where those workflows were discussed.

- interpreter 24x7 local stack on Mac M1: local stack, Mac M1, 24x7, automation stack, hermes
  - desc: Covers older local-stack and automation-discovery work that predates the newer external-drive/oracle consolidation. Search after the newer 2026-08-07 topics if you need historical context rather than the current preferred setup.

#### 2026-08-09

- Project workspace setup and continuity: PROJECTS.md, /Volumes/External/dev, workspace continuity, session memory
  - desc: This session set up the project workflow. User wants to use `/Volumes/External/dev/` as the main project folder with PROJECTS.md as the navigation hub. The file PROJECTS.md is at `/Volumes/External/dev/PROJECTS.md` and lists all 12 projects. The user wants me to remember session context and restore continuity after restart.
  - learnings: There is no built-in tab/session restore in Interpreter. However, memory_summary.md + MEMORY.md serve as externalized memory across sessions. After this session, the next session should:
    1. Read memory_summary.md and MEMORY.md to restore context
    2. Open PROJECTS.md in a tab (`interpreter-app tools builtin-interpreter interpreter_set --json '{"path": "tree.tabs", "value": [{"path": "/Volumes/External/dev/PROJECTS.md"}]}'`)
    3. Open the left sidebar explorer (`interpreter-app layout set sidebars.left.is_open true`)
    4. Set workspace to /Volumes/External/dev in config (`interpreter-app config set lastWorkspace /Volumes/External/dev`)
    5. Offer to continue from where the user left off
  - Project list: agents-toolkit, artifacts, hermes-webui, it-operations-framework, meeting-pipeline, my-project, open-interpreter, project-notes, scheduled-skills, transcribe-bot, transcribe-service, uz-market-bot
  - User confirmed: подход устраивает, сказал "да давай, дорабатывай себя и учись"
