#!/usr/bin/env bash
# Setup script for multi-agent-analyst skill
# Creates a venv and installs dependencies
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$SKILL_DIR/.venv"

echo "📦 Setting up multi-agent-analyst environment..."
echo "   Skill dir: $SKILL_DIR"

# Create venv if needed
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "   ✅ Created venv at $VENV_DIR"
fi

# Install
"$VENV_DIR/bin/pip" install --quiet -r "$SKILL_DIR/requirements.txt"
echo "   ✅ Dependencies installed"

echo ""
echo "🚀 Usage:"
echo "   export OPENROUTER_API_KEY='sk-or-v1-...'"
echo "   $VENV_DIR/bin/python $SKILL_DIR/scripts/optimized_agent_router.py"
echo ""
