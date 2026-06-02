"""Cluster size value object — allocation unit size for the filesystem."""

from enum import Enum, unique


@unique
class ClusterSize(int, Enum):
    """Allocation unit sizes in bytes for filesystem formatting.

    Smaller clusters waste less space but increase metadata overhead.
    Larger clusters improve sequential I/O but increase internal fragmentation.
    DEFAULT lets mkfs choose the optimal size for the drive.
    """

    DEFAULT = 0
    BYTES_512 = 512
    BYTES_1K = 1024
    BYTES_2K = 2048
    BYTES_4K = 4096
    BYTES_8K = 8192
    BYTES_16K = 16384
    BYTES_32K = 32768
    BYTES_64K = 65536

    def label(self) -> str:
        """Return a human-readable label for display in the UI."""
        if self == ClusterSize.DEFAULT:
            return "Default"
        size = int(self)
        if size >= 1024:
            return f"{size // 1024} KB"
        return f"{size} bytes"
