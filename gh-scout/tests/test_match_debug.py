#!/usr/bin/env python3
"""Локальный тест: какие слова матчатся в реальных секциях unsloth."""
import sys, re, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.feature_extractor import FeatureExtractor, OUR_PROJECTS_KEYWORDS

BODY = """Run Qwen3.8-Flash-Next and GLM-5.3-Flash up to 2x faster with MTP. MTP is enabled by default, you can still disable it.
Also our new release includes 170+ training, chat, hardware, and performance improvements.

## Highlights
*  **Smoother model loading** (less errors) across local servers and connected providers.
* Faster and less laggy UI with follow-up turns much faster for all chats.
*  **Safer chat edits** that preserve tool cards, reply details, and conversation branches.
* **New lo

## What's Changed
* Put the smart offload planner back behind its flag by @aaron
* Fix memory fragmentation by @bob
* Add MTP support for GLM-5.3 by @carol

## Audio
* Added support for MiniMax-Music3, Higgs, MOSS audio models.
* Audio model loading is now faster.

## Chat + tools
- Run several tool calls at once without mixing up their arguments.
- Chat history is now compressed automatically.
"""

class FakeRelease:
    body = BODY
    id = 1

ex = FeatureExtractor()
features = ex.extract_features(FakeRelease())

print("=== Фичи и конкретные слова-матчи ===")
for f in features:
    if not f["our_projects_tags"]:
        continue
    text_lower = f["description"].lower()
    matches = {}
    for proj in f["our_projects_tags"]:
        kws = [kw for kw in OUR_PROJECTS_KEYWORDS[proj]
               if re.search(rf"\b{re.escape(kw)}\b", text_lower)]
        matches[proj] = kws
    print(f"  [{f['title'][:45]}]")
    for proj, kws in matches.items():
        print(f"    {proj}: {kws}")
    print(f"    section: {f['description'][:90]!r}")
