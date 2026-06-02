#!/usr/bin/env bash
# Builds a FluxDrive AppImage using linuxdeploy + appimagetool.
# Called by CI workflows and the dev-release.sh script.
#
# Required env vars:
#   VERSION — full version string (e.g. "0.1.0" or "0.1.0-dev.20240601.abc123")
#
# Optionally set ARCH (default: x86_64)

set -euo pipefail

VERSION="${VERSION:-$(python3 -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(d['project']['version'])")}"
ARCH="${ARCH:-x86_64}"

# linuxdeploy-plugin-qt requires QMAKE to point to qmake6 on Ubuntu 22.04+
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
PIP="${PIP:-$(command -v pip3 2>/dev/null || command -v pip 2>/dev/null || echo "python3 -m pip")}"
cd "${ROOT}"
${PIP} install --quiet --prefix="${APPDIR}/usr" --no-deps -e .
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

# ─── AppRun (set before and after linuxdeploy to prevent overwrite) ───────
_install_apprun() {
    cp "${ROOT}/packaging/AppDir/AppRun" "${APPDIR}/AppRun"
    chmod +x "${APPDIR}/AppRun"
    cp "${ROOT}/packaging/AppDir/fluxdrive.desktop" "${APPDIR}/" 2>/dev/null || \
        cp "${APPDIR}/usr/share/applications/fluxdrive.desktop" "${APPDIR}/"
}
_install_apprun

# ─── Download tools ───────────────────────────────────────────────────────
_download() {
    local dest="$1" url="$2"
    [[ -f "${dest}" ]] && return 0
    echo "→ Downloading $(basename "${dest}")…"
    wget -q -O "${dest}" "${url}"
}

LINUXDEPLOY="${BUILD_DIR}/linuxdeploy-${ARCH}.AppImage"
_download "${LINUXDEPLOY}" \
    "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-${ARCH}.AppImage"
chmod +x "${LINUXDEPLOY}"

PLUGIN_QT="${BUILD_DIR}/linuxdeploy-plugin-qt-${ARCH}.AppImage"
_download "${PLUGIN_QT}" \
    "https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-${ARCH}.AppImage"
chmod +x "${PLUGIN_QT}"

# appimagetool is used separately so we can embed the newer type2 runtime
# which handles FUSE-blocked environments (Fedora/SELinux, Aurora OS, etc.)
APPIMAGETOOL="${BUILD_DIR}/appimagetool-${ARCH}.AppImage"
_download "${APPIMAGETOOL}" \
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
chmod +x "${APPIMAGETOOL}"

# The newer type2-runtime falls back to extract-and-run when FUSE execution
# is blocked by SELinux or kernel restrictions, without user intervention.
RUNTIME="${BUILD_DIR}/runtime-${ARCH}"
_download "${RUNTIME}" \
    "https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-${ARCH}"

# ─── Deploy Qt dependencies (no AppImage output — appimagetool handles that) ─
echo "→ Deploying Qt dependencies…"
APPIMAGE_EXTRACT_AND_RUN=1 QMAKE="${QMAKE}" ARCH="${ARCH}" \
"${LINUXDEPLOY}" \
    --appdir "${APPDIR}" \
    --plugin qt \
    --desktop-file "${APPDIR}/fluxdrive.desktop" \
    --icon-file "${APPDIR}/usr/share/icons/hicolor/256x256/apps/fluxdrive.png" || \
APPIMAGE_EXTRACT_AND_RUN=1 ARCH="${ARCH}" \
"${LINUXDEPLOY}" \
    --appdir "${APPDIR}" \
    --desktop-file "${APPDIR}/fluxdrive.desktop" \
    --icon-file "${APPDIR}/usr/share/icons/hicolor/256x256/apps/fluxdrive.png"

# Restore AppRun — linuxdeploy may replace it with a generic launcher
_install_apprun

# ─── Build AppImage with updated type2 runtime ────────────────────────────
echo "→ Building AppImage with updated runtime…"
OUTPUT_FILE="${DIST_DIR}/FluxDrive-${VERSION}-${ARCH}.AppImage"

ARCH="${ARCH}" APPIMAGE_EXTRACT_AND_RUN=1 \
"${APPIMAGETOOL}" \
    --runtime-file "${RUNTIME}" \
    "${APPDIR}" \
    "${OUTPUT_FILE}"

chmod +x "${OUTPUT_FILE}"

# ─── Launcher script (Fedora / SELinux / Aurora OS compatibility) ─────────
# On systems where FUSE execution is restricted by SELinux (Fedora, Aurora,
# Silverblue, etc.) the AppImage runtime cannot exec AppRun from the FUSE
# mount point. APPIMAGE_EXTRACT_AND_RUN=1 makes the runtime extract the
# squashfs to a regular tmpfs directory instead, bypassing the restriction.
LAUNCHER_FILE="${DIST_DIR}/FluxDrive-${VERSION}-${ARCH}.sh"
cat > "${LAUNCHER_FILE}" << LAUNCHER
#!/usr/bin/env bash
# FluxDrive launcher — use this on Fedora / Aurora OS / SELinux systems
# instead of running the .AppImage directly.
SCRIPT_DIR="\$(dirname "\$(readlink -f "\${BASH_SOURCE[0]}")")"
export APPIMAGE_EXTRACT_AND_RUN=1
exec "\${SCRIPT_DIR}/FluxDrive-${VERSION}-${ARCH}.AppImage" "\$@"
LAUNCHER
chmod +x "${LAUNCHER_FILE}"

# ─── Checksum ─────────────────────────────────────────────────────────────
cd "${DIST_DIR}"
sha256sum "$(basename "${OUTPUT_FILE}")" > "FluxDrive-${VERSION}-${ARCH}.AppImage.sha256"

echo ""
echo "✓ AppImage : ${OUTPUT_FILE}"
echo "✓ Launcher : ${LAUNCHER_FILE}  (use on Fedora/Aurora/SELinux)"
echo "✓ SHA256   : ${DIST_DIR}/FluxDrive-${VERSION}-${ARCH}.AppImage.sha256"
