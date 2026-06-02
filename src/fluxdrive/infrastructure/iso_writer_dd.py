"""DD-mode ISO writer — byte-for-byte copy using dd."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from fluxdrive.application.contracts.i_iso_writer import IIsoWriter
from fluxdrive.domain.entities.write_config import WriteConfig
from fluxdrive.domain.exceptions.write_errors import WriteError
from fluxdrive.domain.value_objects.write_mode import WriteMode

_DD_BLOCK_SIZE = "4M"  # 4 MiB blocks balance throughput and progress granularity


class DdIsoWriter(IIsoWriter):
    """Writes an ISO image to a device using dd (byte-for-byte mode).

    This writer cannot create persistent partitions and does not
    install a separate bootloader — the ISO's boot sectors are
    preserved exactly as-is by the raw copy.
    """

    def can_handle(self, config: WriteConfig) -> bool:
        """Return True when the config specifies DD image write mode.

        Args:
            config: The write configuration to evaluate.
        """
        return config.write_mode == WriteMode.DD_IMAGE

    def write(
        self,
        config: WriteConfig,
        progress_callback: Callable[[int, str], None],
    ) -> None:
        """Write the ISO to the device using dd with progress tracking.

        Args:
            config: Write configuration (iso_image must be set).
            progress_callback: Called with (percent: int, message: str).

        Raises:
            WriteError: If dd exits with a non-zero code.
        """
        if config.iso_image is None:
            raise WriteError("DD writer requires an ISO image.")

        iso_path = str(config.iso_image.path)
        device_path = str(config.device.path)
        total_bytes = config.iso_image.size_bytes

        progress_callback(0, f"Writing {config.iso_image.filename()} → {device_path}…")

        self._run_dd(iso_path, device_path, total_bytes, progress_callback)
        self._sync_device(device_path, progress_callback)

        progress_callback(100, "Write complete.")

    def _run_dd(
        self,
        iso_path: str,
        device_path: str,
        total_bytes: int,
        progress_callback: Callable[[int, str], None],
    ) -> None:
        """Execute dd and parse its status output for progress reporting.

        Args:
            iso_path: Source ISO file path.
            device_path: Target block device path.
            total_bytes: Total bytes to write (used for progress).
            progress_callback: Progress reporting callback.

        Raises:
            WriteError: If dd returns a non-zero exit code.
        """
        cmd = [
            "dd",
            f"if={iso_path}",
            f"of={device_path}",
            f"bs={_DD_BLOCK_SIZE}",
            "status=progress",
            "oflag=sync",
        ]

        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            text=True,
        )

        assert process.stderr is not None
        for line in process.stderr:
            written = self._parse_dd_progress(line)
            if written is not None and total_bytes > 0:
                percent = min(99, int(written * 100 / total_bytes))
                speed = self._extract_speed(line)
                progress_callback(percent, f"Writing… {speed}")

        process.wait()
        if process.returncode not in (0, None):
            raise WriteError(f"dd failed with exit code {process.returncode}")

    def _parse_dd_progress(self, line: str) -> int | None:
        """Extract bytes-written count from a dd status=progress line.

        Args:
            line: One line from dd's stderr output.

        Returns:
            Bytes written as int, or None if the line is not a progress line.
        """
        try:
            parts = line.strip().split()
            if parts and parts[0].isdigit():
                return int(parts[0])
        except (ValueError, IndexError):
            pass
        return None

    def _extract_speed(self, line: str) -> str:
        """Extract the transfer speed string from a dd status line.

        Args:
            line: One line from dd's stderr output.

        Returns:
            Speed string like '120 MB/s', or empty string if not found.
        """
        if "," in line:
            parts = line.split(",")
            if len(parts) >= 3:
                return parts[-1].strip().split()[0] + " " + parts[-1].strip().split()[-1]
        return ""

    def _sync_device(
        self,
        device_path: str,
        progress_callback: Callable[[int, str], None],
    ) -> None:
        """Flush all kernel write buffers to the device.

        Args:
            device_path: Block device path string.
            progress_callback: Progress reporting callback.
        """
        progress_callback(99, "Flushing write buffers…")
        subprocess.run(["sync"], check=True)
        subprocess.run(
            ["blockdev", "--flushbufs", device_path],
            capture_output=True,
        )


def _derive_partition(device_path: str) -> Path:
    """Derive the first partition path from a disk device path.

    Args:
        device_path: Disk device path string.
    """
    if device_path[-1].isdigit():
        return Path(f"{device_path}p1")
    return Path(f"{device_path}1")
