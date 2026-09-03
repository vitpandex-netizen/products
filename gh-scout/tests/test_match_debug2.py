#!/usr/bin/env python3
"""Локальный тест: матчинг на ПОЛНОМ body unsloth v0.1.805 (28K)."""
import sys, re, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.feature_extractor import FeatureExtractor, OUR_PROJECTS_KEYWORDS

# Реальный body из релиза (сохранён при диагностике)
BODY = """Run Qwen3.8-Flash-Next and GLM-5.3-Flash up to 2x faster with MTP. MTP is enabled by default, you can still disable it.
Also our new release includes 170+ training, chat, hardware, and performance improvements.

## Highlights
*  **Smoother model loading** (less errors) across local servers and connected providers.
* Faster and less laggy UI with follow-up turns much faster for all chats.
*  **Safer chat edits** that preserve tool cards, reply details, and conversation branches.
* **New low

## Chat + tools
- Run several tool calls at once without mixing up their arguments.
- Chat history is now compressed automatically.
- Better agent tool calling across providers.
- **Insight**: conversations now preserve tool cards across branches.

## What's Changed
* Put the smart offload planner back behind its flag by @danielhanc
* Fix memory fragmentation by @bob
* Bump install script version by @carol
"""

class FakeRelease:
    body = BODY
    id = 1

ex = FeatureExtractor()
features = ex.extract_features(FakeRelease())

print("=== Фичи с матчами ===")
for f in features:
    if not f["our_projects_tags"]:
        continue
    text_lower = f["description"].lower()
    matches = {}
    for proj in f["our_projects_tags"]:
        kws = [kw for kw in OUR_PROJECTS_KEYWORDS[proj]
               if re.search(rf"\b{re.escape(kw)}\b", text_lower)]
        matches[proj] = kws
    print(f"  [{f['title'][:50]}] rel={f['relevance']:.2f}")
    for proj, kws in matches.items():
        print(f"    {proj} -> {kws}")
