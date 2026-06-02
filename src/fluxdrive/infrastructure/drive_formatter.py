"""Drive formatter — partitions and creates filesystems on a USB device."""

import subprocess
from collections.abc import Callable
from pathlib import Path

from fluxdrive.application.contracts.i_drive_formatter import IDriveFormatter
from fluxdrive.domain.entities.write_config import WriteConfig
from fluxdrive.domain.exceptions.write_errors import FormatError, PartitioningError
from fluxdrive.domain.value_objects.file_system import FileSystem
from fluxdrive.domain.value_objects.partition_scheme import PartitionScheme


class DriveFormatter(IDriveFormatter):
    """Partitions and formats a USB device using system tools (parted, mkfs.*).

    Uses a two-step process:
    1. Create partition table (parted).
    2. Create filesystem on the first partition (mkfs.*).
    """

    def format(
        self,
        config: WriteConfig,
        progress_callback: Callable[[int, str], None],
    ) -> None:
        """Partition and format the target device.

        Args:
            config: Write configuration with all formatting parameters.
            progress_callback: Called with (percent: int, message: str).
        """
        device_path = str(config.device.path)

        progress_callback(0, f"Partitioning {device_path}…")
        self._create_partition_table(device_path, config.partition_scheme)

        progress_callback(30, "Creating primary partition…")
        partition = self._create_primary_partition(device_path)

        progress_callback(60, f"Formatting with {config.file_system.label()}…")
        self._create_filesystem(
            partition,
            config.file_system,
            config.volume_label,
            config.cluster_size,
        )

        progress_callback(100, "Format complete.")

    def _create_partition_table(
        self,
        device_path: str,
        scheme: PartitionScheme,
    ) -> None:
        """Write a new partition table to the device.

        Args:
            device_path: Block device path string.
            scheme: MBR or GPT partition scheme.

        Raises:
            PartitioningError: If parted exits with a non-zero code.
        """
        label = "msdos" if scheme == PartitionScheme.MBR else "gpt"
        result = subprocess.run(
            ["parted", "-s", device_path, "mklabel", label],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise PartitioningError(
                f"parted mklabel failed: {result.stderr.strip()}"
            )

    def _create_primary_partition(self, device_path: str) -> str:
        """Create a single primary partition spanning the entire device.

        Args:
            device_path: Block device path string.

        Returns:
            Partition device path (e.g. '/dev/sdb1').

        Raises:
            PartitioningError: If parted exits with a non-zero code.
        """
        result = subprocess.run(
            ["parted", "-s", device_path, "mkpart", "primary", "0%", "100%"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise PartitioningError(
                f"parted mkpart failed: {result.stderr.strip()}"
            )

        partition = self._derive_partition_path(device_path)
        self._wait_for_partition(partition)
        return partition

    def _derive_partition_path(self, device_path: str) -> str:
        """Derive the partition device path from the disk device path.

        Args:
            device_path: Disk device path (e.g. '/dev/sdb').

        Returns:
            First partition path (e.g. '/dev/sdb1').
        """
        if device_path[-1].isdigit():
            return f"{device_path}p1"
        return f"{device_path}1"

    def _wait_for_partition(self, partition: str) -> None:
        """Wait until the partition node appears in /dev.

        Args:
            partition: Expected partition device path.

        Raises:
            PartitioningError: If the partition does not appear within 10 seconds.
        """
        import time

        deadline = time.monotonic() + 10.0
        while not Path(partition).exists():
            if time.monotonic() > deadline:
                raise PartitioningError(
                    f"Partition device {partition} did not appear after 10 seconds."
                )
            time.sleep(0.2)

    def _create_filesystem(
        self,
        partition: str,
        fs: FileSystem,
        label: str,
        cluster_size: object,
    ) -> None:
        """Run the appropriate mkfs command for the selected filesystem.

        Args:
            partition: Partition device path.
            fs: Filesystem type to create.
            label: Volume label (may be empty).
            cluster_size: ClusterSize value object (0 = auto).

        Raises:
            FormatError: If the mkfs command fails.
        """
        cmd = self._build_mkfs_command(partition, fs, label, cluster_size)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise FormatError(
                f"{cmd[0]} failed: {result.stderr.strip()}"
            )

    def _build_mkfs_command(
        self,
        partition: str,
        fs: FileSystem,
        label: str,
        cluster_size: object,
    ) -> list[str]:
        """Build the mkfs command arguments for the selected filesystem.

        Args:
            partition: Partition device path.
            fs: Filesystem type.
            label: Volume label.
            cluster_size: ClusterSize enum value (int).

        Returns:
            Command list ready for subprocess.run().
        """
        cmd = [fs.mkfs_command()]

        if label:
            label_flags = {
                FileSystem.FAT32: ["-n"],
                FileSystem.LARGE_FAT32: ["-n"],
                FileSystem.NTFS: ["-L"],
                FileSystem.EXFAT: ["-L"],
                FileSystem.EXT4: ["-L"],
                FileSystem.UDF: ["-l"],
            }
            flags = label_flags.get(fs, ["-L"])
            cmd.extend(flags)
            cmd.append(label[:11] if fs in (FileSystem.FAT32, FileSystem.LARGE_FAT32) else label)

        cluster_int = int(cluster_size)  # type: ignore[arg-type]
        if cluster_int > 0:
            cluster_flags = {
                FileSystem.FAT32: ["-S", str(cluster_int)],
                FileSystem.NTFS: ["-c", str(cluster_int)],
                FileSystem.EXT4: ["-b", str(cluster_int)],
            }
            extra = cluster_flags.get(fs)
            if extra:
                cmd.extend(extra)

        if fs == FileSystem.FAT32:
            cmd.extend(["-F", "32"])
        elif fs == FileSystem.LARGE_FAT32:
            cmd.extend(["-F", "32"])
        elif fs == FileSystem.NTFS:
            cmd.extend(["-f"])

        cmd.append(partition)
        return cmd
