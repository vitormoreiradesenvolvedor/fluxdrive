"""Bad block checker — uses badblocks or dd-verify to check drive integrity."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from fluxdrive.application.contracts.i_block_checker import IBlockChecker
from fluxdrive.domain.exceptions.write_errors import BadBlocksError


class BadBlockChecker(IBlockChecker):
    """Checks a storage device for bad blocks using the badblocks utility.

    Falls back to a dd-based read-verify if badblocks is unavailable.
    Reports progress as (blocks_checked, bad_blocks_found, message).
    """

    def check(
        self,
        device_path: Path,
        passes: int,
        progress_callback: Callable[[int, int, str], None],
    ) -> int:
        """Run bad-block detection on the given device.

        Args:
            device_path: Path to the block device.
            passes: Number of verification passes (1–4).
            progress_callback: Called with (blocks_checked, bad_blocks, message).

        Returns:
            Number of bad blocks found.

        Raises:
            BadBlocksError: If a fatal I/O error prevents completion.
        """
        if self._badblocks_available():
            return self._run_badblocks(device_path, passes, progress_callback)
        return self._run_dd_verify(device_path, progress_callback)

    def _badblocks_available(self) -> bool:
        """Return True if the badblocks command is installed.

        Returns:
            True when badblocks is found in the system PATH.
        """
        result = subprocess.run(
            ["which", "badblocks"],
            capture_output=True,
        )
        return result.returncode == 0

    def _run_badblocks(
        self,
        device_path: Path,
        passes: int,
        progress_callback: Callable[[int, int, str], None],
    ) -> int:
        """Execute badblocks and parse its output for progress and results.

        Args:
            device_path: Block device path.
            passes: Number of passes.
            progress_callback: Progress reporting callback.

        Returns:
            Number of bad blocks found.
        """
        mode = "-w" if passes > 1 else "-n"
        cmd = ["badblocks", "-v", mode, str(device_path)]

        progress_callback(0, 0, f"Starting bad block check ({passes} passes)…")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        bad_count = self._count_bad_blocks(result.stdout + result.stderr)
        progress_callback(100, bad_count, "Bad block check complete.")
        return bad_count

    def _run_dd_verify(
        self,
        device_path: Path,
        progress_callback: Callable[[int, int, str], None],
    ) -> int:
        """Perform a read-only dd pass as a fallback bad-block check.

        Args:
            device_path: Block device path.
            progress_callback: Progress reporting callback.

        Returns:
            0 if readable, raises BadBlocksError on I/O error.
        """
        progress_callback(0, 0, "Running dd read verification…")

        result = subprocess.run(
            [
                "dd",
                f"if={device_path}",
                "of=/dev/null",
                "bs=4M",
                "status=progress",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise BadBlocksError(
                f"Read verification failed: {result.stderr.strip()}"
            )

        progress_callback(100, 0, "Read verification complete — no errors detected.")
        return 0

    def _count_bad_blocks(self, output: str) -> int:
        """Count the number of bad blocks reported in badblocks output.

        Args:
            output: Combined stdout + stderr from badblocks.

        Returns:
            Number of bad block entries found in the output.
        """
        count = 0
        for line in output.splitlines():
            stripped = line.strip()
            if stripped and stripped[0].isdigit():
                count += 1
        return count
