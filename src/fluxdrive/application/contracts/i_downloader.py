"""Interface for ISO downloading."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DownloadableIso:
    """Metadata for a downloadable ISO image.

    Attributes:
        name: Human-readable distribution name (e.g. 'Ubuntu 24.04 LTS').
        url: Direct download URL.
        size_bytes: Expected file size in bytes (0 if unknown).
        sha256: Expected SHA-256 digest (empty if not provided).
        version: Version string (e.g. '24.04').
        architecture: CPU architecture string (e.g. 'amd64', 'arm64').
    """

    name: str
    url: str
    size_bytes: int
    sha256: str
    version: str
    architecture: str


class IDownloader(ABC):
    """Contract for downloading ISO files from remote URLs."""

    @abstractmethod
    def list_available(self) -> list[DownloadableIso]:
        """Return a list of curated downloadable ISO images.

        Returns:
            List of DownloadableIso descriptors for popular distributions.
        """

    @abstractmethod
    def download(
        self,
        iso: DownloadableIso,
        destination: Path,
        progress_callback: Callable[[int, int, int], None],
    ) -> Path:
        """Download an ISO to the destination directory.

        Args:
            iso: The ISO to download.
            destination: Directory where the file will be saved.
            progress_callback: Called with (bytes_downloaded, total_bytes, speed_bps).

        Returns:
            Path to the downloaded file.

        Raises:
            DownloadError: If the download fails or is interrupted.
        """
