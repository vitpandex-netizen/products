"""Test the new FeatureExtractor against real release bodies."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.feature_extractor import FeatureExtractor

# Real release bodies from our DB
TEST_BODIES = [
    # Semantica v0.6.7
    """# Semantica v0.6.7

**Released:** 2026-08-28

## What's Changed
- [#1071](https://github.com/semantica-agi/semantica/pull/1071) Fix: preserve semantic index during layer reindexing by @jdoe
- [#1068](https://github.com/semantica-agi/semantica/pull/1068) Add graph traversal API for neighborhood queries by @asmith
- [#1065](https://github.com/semantica-agi/semantica/pull/1065) Optimize vector search with ANN indexes by @bob

## Features
- **New**: Subgraph extraction for community detection
- **New**: Support temporal queries on graph edges

## New Contributors
- @alice made their first contribution in #1071
""",
    # AutoGPT
    """# 🚀 Release autogpt-platform-beta-v0.7.2

## 🔥 What's New?

### New Features
- **#14021** - AI-voice narrative in morning briefing
- **#14022** - Per-expert spend tracking on home team cards
- **#14030** - Launch roster with real workflow bundles
- **#14027** - Writing-style capture for content generation

### Bug Fixes
- Fix WebSocket reconnection backoff
- Fix memory leak in session management
""",
]

fe = FeatureExtractor()

for i, body in enumerate(TEST_BODIES):
    print(f"=== Test {i+1} ===")
    class FakeRelease:
        body = body
        id = i
    features = fe.extract_features(FakeRelease())
    for f in features:
        print(f"  [{f['category']}] {f['title'][:80]}")
        print(f"    relevant: {f['our_projects_tags']} | rel: {f['relevance']:.2f}")
    print(f"  → {len(features)} features extracted")
    print()