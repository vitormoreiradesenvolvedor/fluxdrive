"""File system value object — describes the target filesystem for the USB."""

from enum import Enum, unique


@unique
class FileSystem(str, Enum):
    """Supported file systems for USB formatting.

    FAT32 is the most compatible for UEFI boot.
    NTFS and exFAT support files larger than 4 GB.
    ext4 is native Linux and suitable for Linux-only drives.
    UDF is required by some optical media emulation tools.
    LARGE_FAT32 uses a custom implementation to bypass the 32 GB FAT32 limit.
    """

    FAT32 = "FAT32"
    LARGE_FAT32 = "LARGE_FAT32"
    NTFS = "NTFS"
    EXFAT = "exFAT"
    EXT4 = "ext4"
    UDF = "UDF"

    def label(self) -> str:
        """Return a human-readable label for display in the UI."""
        labels = {
            FileSystem.FAT32: "FAT32 (Default)",
            FileSystem.LARGE_FAT32: "Large FAT32 (> 32 GB drives)",
            FileSystem.NTFS: "NTFS",
            FileSystem.EXFAT: "exFAT",
            FileSystem.EXT4: "ext4",
            FileSystem.UDF: "UDF",
        }
        return labels[self]

    def mkfs_command(self) -> str:
        """Return the Linux mkfs command for this filesystem."""
        commands = {
            FileSystem.FAT32: "mkfs.fat",
            FileSystem.LARGE_FAT32: "mkfs.fat",
            FileSystem.NTFS: "mkfs.ntfs",
            FileSystem.EXFAT: "mkfs.exfat",
            FileSystem.EXT4: "mkfs.ext4",
            FileSystem.UDF: "mkfs.udf",
        }
        return commands[self]

    def supports_large_files(self) -> bool:
        """Return True if this filesystem handles files larger than 4 GB."""
        return self in (FileSystem.NTFS, FileSystem.EXFAT, FileSystem.EXT4, FileSystem.LARGE_FAT32)

    def is_uefi_compatible(self) -> bool:
        """Return True if UEFI firmware can read this filesystem natively."""
        return self in (FileSystem.FAT32, FileSystem.LARGE_FAT32)
