#!/usr/bin/env bash
# setup_worktree.sh — Git Worktree isolation per task
# Usage: ./setup_worktree.sh <task-id> [base-branch]
# Example: ./setup_worktree.sh TASK-BGT-044 main

set -euo pipefail

TASK_ID="${1:?Usage: setup_worktree.sh <task-id> [base-branch]}"
BASE_BRANCH="${2:-main}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREE_DIR="${REPO_ROOT}/.worktrees/${TASK_ID}"

echo "=== Setup Worktree for ${TASK_ID} ==="
echo "Repo: ${REPO_ROOT}"
echo "Base branch: ${BASE_BRANCH}"

# Проверка что мы в git repo
if [[ ! -d "${REPO_ROOT}/.git" ]]; then
    echo "ERROR: Not a git repository at ${REPO_ROOT}"
    exit 1
fi

# Проверка что base-branch существует
if ! git rev-parse --verify "${BASE_BRANCH}" >/dev/null 2>&1; then
    echo "ERROR: Branch '${BASE_BRANCH}' not found"
    git branch -a | head -20
    exit 1
fi

# Проверка что worktree уже существует
if [[ -d "${WORKTREE_DIR}" ]]; then
    echo "WARNING: Worktree already exists at ${WORKTREE_DIR}"
    read -p "Remove and recreate? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    git worktree remove "${WORKTREE_DIR}" --force 2>/dev/null || true
    rm -rf "${WORKTREE_DIR}"
fi

# Создание worktree
git worktree add "${WORKTREE_DIR}" "${BASE_BRANCH}"
echo "✅ Worktree created: ${WORKTREE_DIR}"
echo ""
echo "Next steps:"
echo "  cd ${WORKTREE_DIR}"
echo "  git checkout -b task/${TASK_ID}"
echo "  # implement in isolated tree"
echo "  git add . && git commit -m '[${TASK_ID}]'"
echo "  git push origin task/${TASK_ID}"
echo "  # затем PR в main с ревью"
