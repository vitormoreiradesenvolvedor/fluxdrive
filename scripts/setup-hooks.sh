#!/usr/bin/env bash
# Instala os git hooks locais do projeto.
# Execute após clonar o repositório: bash scripts/setup-hooks.sh

set -euo pipefail

HOOKS_DIR=".githooks"
GIT_HOOKS_DIR=".git/hooks"

if [[ ! -d ".git" ]]; then
    echo "Erro: execute este script na raiz do repositório."
    exit 1
fi

echo "Instalando git hooks..."

for hook in "$HOOKS_DIR"/*; do
    hook_name=$(basename "$hook")
    target="$GIT_HOOKS_DIR/$hook_name"
    cp "$hook" "$target"
    chmod +x "$target"
    echo "  ✓ $hook_name instalado"
done

# Configura git para usar o diretório de hooks do projeto
git config core.hooksPath "$HOOKS_DIR"
echo ""
echo "✓ Hooks instalados em $GIT_HOOKS_DIR/"
echo "✓ git config core.hooksPath definido como $HOOKS_DIR"
echo ""
echo "Os hooks ativos são:"
echo "  pre-commit       — bloqueia commits em master/development"
echo "  pre-push         — bloqueia push em master/development"
echo "  commit-msg       — valida formato Conventional Commits"
echo "  prepare-commit-msg — remove atribuições automáticas indevidas"
