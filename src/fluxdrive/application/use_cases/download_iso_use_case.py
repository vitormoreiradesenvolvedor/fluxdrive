"""Use case for downloading an ISO from a curated remote source."""

from collections.abc import Callable
from pathlib import Path

from fluxdrive.application.contracts.i_downloader import (
    DownloadableIso,
    IDownloader,
)


class DownloadIsoUseCase:
    """Orchestrates ISO download from a remote source.

    Delegates network I/O to the injected IDownloader and exposes
    progress through a callback, keeping UI concerns out of the domain.
    """

    def __init__(self, downloader: IDownloader) -> None:
        """Initialize with a concrete downloader implementation.

        Args:
            downloader: An IDownloader implementation.
        """
        self._downloader = downloader

    def list_sources(self) -> list[DownloadableIso]:
        """Return a list of curated downloadable ISO images.

        Returns:
            List of DownloadableIso descriptors for popular distributions.
        """
        return self._downloader.list_available()

    def download(
        self,
        iso: DownloadableIso,
        destination: Path,
        progress_callback: Callable[[int, int, int], None],
    ) -> Path:
        """Download the selected ISO to the destination directory.

        Args:
            iso: The DownloadableIso descriptor.
            destination: Directory where the downloaded file will be saved.
            progress_callback: Called with (bytes_done, total_bytes, speed_bps).

        Returns:
            Path to the downloaded ISO file.

        Raises:
            DownloadError: If the download fails.
        """
        return self._downloader.download(iso, destination, progress_callback)
