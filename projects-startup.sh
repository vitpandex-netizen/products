#!/bin/zsh
# Ждём пока Interpreter запустится и загрузит интерфейс
sleep 5

# Открываем навигатор проектов
INTERPRETER_CLI="/Users/vitaliyr/Library/Application Support/Interpreter/codex-home/home/.interpreter/runtime/interpreter-cli/shell-safe-bin/interpreter-app"

if [ -f "$INTERPRETER_CLI" ]; then
  "$INTERPRETER_CLI" tools builtin-interpreter interpreter_set --json '{"path": "tree.tabs", "value": [{"path": "/Volumes/External/dev/PROJECTS.md"}]}' 2>/dev/null
  "$INTERPRETER_CLI" layout set sidebars.left.is_open true 2>/dev/null
fi
