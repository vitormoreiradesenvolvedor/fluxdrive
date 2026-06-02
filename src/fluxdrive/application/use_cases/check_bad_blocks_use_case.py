"""Use case for checking a drive for bad blocks."""

from collections.abc import Callable
from pathlib import Path

from fluxdrive.application.contracts.i_block_checker import IBlockChecker


class CheckBadBlocksUseCase:
    """Orchestrates a bad-block detection pass on a storage device.

    Supports 1 to 4 verification passes as in Rufus, where more passes
    provide higher confidence but take longer.
    """

    MAX_PASSES = 4

    def __init__(self, checker: IBlockChecker) -> None:
        """Initialize with a concrete block checker implementation.

        Args:
            checker: An IBlockChecker implementation.
        """
        self._checker = checker

    def execute(
        self,
        device_path: Path,
        passes: int,
        progress_callback: Callable[[int, int, str], None],
    ) -> int:
        """Run bad-block detection on the specified device.

        Args:
            device_path: Path to the block device.
            passes: Number of verification passes (1–4).
            progress_callback: Called with (checked_blocks, bad_blocks, message).

        Returns:
            Number of bad blocks found (0 = healthy drive).

        Raises:
            ValueError: If passes is not between 1 and MAX_PASSES.
            BadBlocksError: If a fatal I/O error occurs.
        """
        if not 1 <= passes <= self.MAX_PASSES:
            raise ValueError(
                f"passes must be between 1 and {self.MAX_PASSES}, got {passes}."
            )
        return self._checker.check(device_path, passes, progress_callback)
