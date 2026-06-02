"""HTTP-based ISO downloader — concrete IDownloader using requests."""

import time
from collections.abc import Callable
from pathlib import Path

import requests

from fluxdrive.application.contracts.i_downloader import DownloadableIso, IDownloader
from fluxdrive.domain.exceptions.write_errors import DownloadError

_CHUNK_SIZE = 1024 * 1024  # 1 MiB per chunk
_TIMEOUT_SECONDS = 30
_CURATED_ISOS: list[DownloadableIso] = [
    DownloadableIso(
        name="Ubuntu 24.04 LTS (Desktop)",
        url="https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.iso",
        size_bytes=5_798_174_720,
        sha256="8762f7e74e4d64d72fceb5f70682e6b069932deedb4949c6975d0f0fe0a91be3",
        version="24.04",
        architecture="amd64",
    ),
    DownloadableIso(
        name="Ubuntu 22.04.4 LTS (Desktop)",
        url="https://releases.ubuntu.com/22.04/ubuntu-22.04.4-desktop-amd64.iso",
        size_bytes=4_983_828_480,
        sha256="45f873de9f8cb637345d6e66a583762730bbea30277ef7b32c9c3bd6700a32b2",
        version="22.04.4",
        architecture="amd64",
    ),
    DownloadableIso(
        name="Fedora Workstation 40",
        url=(
            "https://dl.fedoraproject.org/pub/fedora/linux/releases/40"
            "/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-40-1.14.iso"
        ),
        size_bytes=2_252_341_248,
        sha256="",
        version="40",
        architecture="x86_64",
    ),
    DownloadableIso(
        name="Debian 12.5 (netinst)",
        url=(
            "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd"
            "/debian-12.5.0-amd64-netinst.iso"
        ),
        size_bytes=659_554_304,
        sha256="013f5b44670d81280b5b1bc02455842b250df2f0c6763398feb69af1a805a14f",
        version="12.5.0",
        architecture="amd64",
    ),
    DownloadableIso(
        name="Linux Mint 21.3 Cinnamon",
        url="https://mirrors.kernel.org/linuxmint/stable/21.3/linuxmint-21.3-cinnamon-64bit.iso",
        size_bytes=2_717_908_992,
        sha256="",
        version="21.3",
        architecture="x86_64",
    ),
    DownloadableIso(
        name="Arch Linux (latest)",
        url="https://mirror.rackspace.com/archlinux/iso/latest/archlinux-x86_64.iso",
        size_bytes=0,
        sha256="",
        version="latest",
        architecture="x86_64",
    ),
    DownloadableIso(
        name="openSUSE Tumbleweed (KDE)",
        url=(
            "https://download.opensuse.org/tumbleweed/iso"
            "/openSUSE-Tumbleweed-DVD-x86_64-Current.iso"
        ),
        size_bytes=0,
        sha256="",
        version="Tumbleweed",
        architecture="x86_64",
    ),
    DownloadableIso(
        name="Kali Linux 2024.1",
        url="https://cdimage.kali.org/kali-2024.1/kali-linux-2024.1-installer-amd64.iso",
        size_bytes=0,
        sha256="",
        version="2024.1",
        architecture="amd64",
    ),
]


class RequestsDownloader(IDownloader):
    """Downloads ISO files from remote URLs using the requests library.

    Streams the download in chunks and reports progress via callback.
    Implements retry logic on transient network errors.
    """

    _MAX_RETRIES = 3

    def list_available(self) -> list[DownloadableIso]:
        """Return the curated list of downloadable ISO images.

        Returns:
            Static list of DownloadableIso descriptors.
        """
        return list(_CURATED_ISOS)

    def download(
        self,
        iso: DownloadableIso,
        destination: Path,
        progress_callback: Callable[[int, int, int], None],
    ) -> Path:
        """Download the ISO to the destination directory with progress tracking.

        Args:
            iso: The DownloadableIso descriptor.
            destination: Directory where the file will be saved.
            progress_callback: Called with (bytes_done, total_bytes, speed_bps).

        Returns:
            Path to the downloaded file.

        Raises:
            DownloadError: If the download fails after all retries.
        """
        destination.mkdir(parents=True, exist_ok=True)
        filename = iso.url.split("/")[-1]
        output_path = destination / filename

        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                self._stream_download(iso, output_path, progress_callback)
                return output_path
            except (requests.RequestException, OSError) as exc:
                if attempt == self._MAX_RETRIES:
                    raise DownloadError(
                        f"Download failed after {self._MAX_RETRIES} attempts: {exc}"
                    ) from exc
                time.sleep(2**attempt)

        raise DownloadError("Download failed: unexpected state.")

    def _stream_download(
        self,
        iso: DownloadableIso,
        output_path: Path,
        progress_callback: Callable[[int, int, int], None],
    ) -> None:
        """Perform the HTTP download with streaming chunks.

        Args:
            iso: The DownloadableIso descriptor.
            output_path: Destination file path.
            progress_callback: Called with (bytes_done, total_bytes, speed_bps).

        Raises:
            requests.HTTPError: If the server returns an error status.
        """
        with requests.get(
            iso.url,
            stream=True,
            timeout=_TIMEOUT_SECONDS,
            headers={"User-Agent": "FluxDrive/0.1"},
        ) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", iso.size_bytes))
            downloaded = 0
            start_time = time.monotonic()

            with output_path.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=_CHUNK_SIZE):
                    fh.write(chunk)
                    downloaded += len(chunk)
                    elapsed = time.monotonic() - start_time
                    speed = int(downloaded / elapsed) if elapsed > 0 else 0
                    progress_callback(downloaded, total, speed)
