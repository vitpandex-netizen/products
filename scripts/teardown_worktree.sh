#!/usr/bin/env bash
# teardown_worktree.sh — Cleanup worktree after merge
# Usage: ./teardown_worktree.sh <task-id>

set -euo pipefail

TASK_ID="${1:?Usage: teardown_worktree.sh <task-id>}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREE_DIR="${REPO_ROOT}/.worktrees/${TASK_ID}"

echo "=== Teardown Worktree for ${TASK_ID} ==="

if [[ ! -d "${WORKTREE_DIR}" ]]; then
    echo "Worktree not found: ${WORKTREE_DIR}"
    exit 0
fi

# Проверка что нет незакоммиченных изменений
cd "${WORKTREE_DIR}"
if [[ -n "$(git status --porcelain)" ]]; then
    echo "WARNING: Uncommitted changes in worktree:"
    git status --porcelain
    read -p "Force remove anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 1
    fi
fi

git worktree remove "${WORKTREE_DIR}" --force
rm -rf "${WORKTREE_DIR}"
echo "✅ Worktree removed: ${WORKTREE_DIR}"
