#!/usr/bin/env bash
# Gera uma build de desenvolvimento local (AppImage) para testes.
# Não requer CI — roda na máquina do desenvolvedor.
#
# Uso: bash scripts/dev-release.sh [--clean]

set -euo pipefail

CLEAN=0
for arg in "$@"; do
    [[ "$arg" == "--clean" ]] && CLEAN=1
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ─── Verifica dependências ─────────────────────────────────────────────────
check_dep() {
    if ! command -v "$1" &>/dev/null; then
        echo "Dependência ausente: $1 — instale com: $2"
        exit 1
    fi
}

check_dep python3 "sudo dnf install python3"
check_dep pip3    "sudo dnf install python3-pip"

# ─── Versão ───────────────────────────────────────────────────────────────
BASE_VERSION=$(python3 -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(d['project']['version'])")
TIMESTAMP=$(date '+%Y%m%d.%H%M%S')
SHORT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "nobranch")
VERSION="${BASE_VERSION}-dev.${TIMESTAMP}.${SHORT_SHA}"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║         FLUXDRIVE — Dev Release Builder          ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Versão  : $VERSION"
echo "║  Branch  : $BRANCH"
echo "║  Commit  : $SHORT_SHA"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ─── Limpeza opcional ─────────────────────────────────────────────────────
if [[ $CLEAN -eq 1 ]]; then
    echo "→ Limpando builds anteriores..."
    rm -rf dist/ build/ *.AppImage AppDir/
fi

# ─── Instala dependências de desenvolvimento ──────────────────────────────
echo "→ Instalando dependências..."
pip3 install -e ".[dev]" --quiet

# ─── Executa testes rápidos (unit apenas) ─────────────────────────────────
echo "→ Executando testes unitários..."
python3 -m pytest tests/unit/ -q --tb=short 2>&1 || {
    echo ""
    echo "✗ Testes falharam. Corrija antes de gerar a build."
    exit 1
}
echo "✓ Testes passaram"

# ─── Gera AppImage ────────────────────────────────────────────────────────
echo "→ Gerando AppImage de desenvolvimento..."
VERSION="$VERSION" bash packaging/build-appimage.sh

# ─── Resultado ────────────────────────────────────────────────────────────
APPIMAGE=$(find dist/ -name "*.AppImage" -newer pyproject.toml 2>/dev/null | head -1)
if [[ -z "$APPIMAGE" ]]; then
    echo "✗ AppImage não encontrado em dist/"
    exit 1
fi

SIZE=$(du -sh "$APPIMAGE" | cut -f1)
SHA256=$(sha256sum "$APPIMAGE" | cut -d' ' -f1)

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Build de desenvolvimento gerada com sucesso!            ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Arquivo : $APPIMAGE"
echo "║  Tamanho : $SIZE"
echo "║  SHA256  : ${SHA256:0:32}..."
LAUNCHER="${APPIMAGE%.AppImage}.sh"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Executar (Ubuntu / Arch / Debian):                      ║"
echo "║    ./$APPIMAGE"
echo "║  Executar (Fedora / Aurora OS / SELinux):                ║"
echo "║    ./$LAUNCHER"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
