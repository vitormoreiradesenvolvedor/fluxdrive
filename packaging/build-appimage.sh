#!/usr/bin/env bash
# Builds a FluxDrive AppImage using linuxdeploy + linuxdeploy-plugin-appimage.
# Called by CI workflows and the dev-release.sh script.
#
# Required env vars:
#   VERSION — full version string (e.g. "0.1.0" or "0.1.0-dev.20240601.abc123")
#
# Optionally set ARCH (default: x86_64)

set -euo pipefail

VERSION="${VERSION:-$(python3 -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(d['project']['version'])")}"
ARCH="${ARCH:-x86_64}"

# linuxdeploy-plugin-qt requires QMAKE to be set to qmake6 on Ubuntu 22.04+
if [[ -z "${QMAKE:-}" ]]; then
    QMAKE="$(command -v qmake6 2>/dev/null || command -v qmake 2>/dev/null || true)"
    export QMAKE
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT}/dist"
BUILD_DIR="${ROOT}/build/appimage"
APPDIR="${BUILD_DIR}/AppDir"

echo "Building FluxDrive AppImage v${VERSION} (${ARCH})…"
mkdir -p "${DIST_DIR}" "${APPDIR}/usr/"{bin,lib,share/{applications,icons/hicolor/256x256/apps}}

# ─── Install app into AppDir ──────────────────────────────────────────────
cd "${ROOT}"
pip install --quiet --prefix="${APPDIR}/usr" --no-deps -e .
cp -r "${ROOT}/src/fluxdrive" "${APPDIR}/usr/lib/python3/dist-packages/" 2>/dev/null || true

# ─── Desktop entry ────────────────────────────────────────────────────────
cat > "${APPDIR}/usr/share/applications/fluxdrive.desktop" << DESKTOP
[Desktop Entry]
Name=FluxDrive
Comment=Bootable USB Creator for Linux
Exec=fluxdrive
Icon=fluxdrive
Type=Application
Categories=System;Utility;
Keywords=USB;ISO;Boot;Bootable;Flash;
DESKTOP

# ─── Icon ─────────────────────────────────────────────────────────────────
if [[ -f "${ROOT}/packaging/fluxdrive.png" ]]; then
    cp "${ROOT}/packaging/fluxdrive.png" \
       "${APPDIR}/usr/share/icons/hicolor/256x256/apps/fluxdrive.png"
fi

# ─── AppRun ───────────────────────────────────────────────────────────────
cp "${ROOT}/packaging/AppDir/AppRun" "${APPDIR}/AppRun"
chmod +x "${APPDIR}/AppRun"
cp "${ROOT}/packaging/AppDir/fluxdrive.desktop" "${APPDIR}/" 2>/dev/null || \
    cp "${APPDIR}/usr/share/applications/fluxdrive.desktop" "${APPDIR}/"

# ─── Download linuxdeploy if needed ───────────────────────────────────────
LINUXDEPLOY="${BUILD_DIR}/linuxdeploy-${ARCH}.AppImage"
if [[ ! -f "${LINUXDEPLOY}" ]]; then
    echo "→ Downloading linuxdeploy…"
    wget -q -O "${LINUXDEPLOY}" \
        "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-${ARCH}.AppImage"
    chmod +x "${LINUXDEPLOY}"
fi

PLUGIN_QT="${BUILD_DIR}/linuxdeploy-plugin-qt-${ARCH}.AppImage"
if [[ ! -f "${PLUGIN_QT}" ]]; then
    echo "→ Downloading linuxdeploy-plugin-qt…"
    wget -q -O "${PLUGIN_QT}" \
        "https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-${ARCH}.AppImage"
    chmod +x "${PLUGIN_QT}"
fi

# ─── Build AppImage ───────────────────────────────────────────────────────
echo "→ Building AppImage…"
OUTPUT_FILE="${DIST_DIR}/FluxDrive-${VERSION}-${ARCH}.AppImage"

ARCH="${ARCH}" \
OUTPUT="${OUTPUT_FILE}" \
"${LINUXDEPLOY}" \
    --appdir "${APPDIR}" \
    --plugin qt \
    --output appimage \
    --desktop-file "${APPDIR}/fluxdrive.desktop" \
    --icon-file "${APPDIR}/usr/share/icons/hicolor/256x256/apps/fluxdrive.png" 2>/dev/null || \
ARCH="${ARCH}" \
OUTPUT="${OUTPUT_FILE}" \
"${LINUXDEPLOY}" \
    --appdir "${APPDIR}" \
    --output appimage \
    --desktop-file "${APPDIR}/fluxdrive.desktop"

chmod +x "${OUTPUT_FILE}"

# ─── Checksum ─────────────────────────────────────────────────────────────
cd "${DIST_DIR}"
sha256sum "$(basename "${OUTPUT_FILE}")" > "FluxDrive-${VERSION}-${ARCH}.AppImage.sha256"

echo ""
echo "✓ AppImage: ${OUTPUT_FILE}"
echo "✓ SHA256:   ${DIST_DIR}/FluxDrive-${VERSION}-${ARCH}.AppImage.sha256"
