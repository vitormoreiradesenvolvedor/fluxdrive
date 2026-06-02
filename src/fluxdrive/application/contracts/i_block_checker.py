"""Interface for bad-block checking."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path


class IBlockChecker(ABC):
    """Contract for verifying drive integrity via bad-block detection."""

    @abstractmethod
    def check(
        self,
        device_path: Path,
        passes: int,
        progress_callback: Callable[[int, int, str], None],
    ) -> int:
        """Run bad-block detection on the given device.

        Args:
            device_path: Path to the block device to check.
            passes: Number of read/write verification passes (1-4).
            progress_callback: Called with (blocks_checked, bad_blocks, status_message).

        Returns:
            Number of bad blocks found (0 means the drive is healthy).

        Raises:
            BadBlocksError: If a fatal I/O error occurs during checking.
        """
