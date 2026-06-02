"""Partition scheme value object — defines how the drive is partitioned."""

from enum import Enum, unique


@unique
class PartitionScheme(str, Enum):
    """Supported partition table types for bootable USB creation.

    MBR supports legacy BIOS and is compatible with all machines.
    GPT is required for drives larger than 2 TB and for pure UEFI systems.
    """

    MBR = "MBR"
    GPT = "GPT"

    def label(self) -> str:
        """Return a human-readable label for display in the UI."""
        labels = {
            PartitionScheme.MBR: "MBR (Master Boot Record)",
            PartitionScheme.GPT: "GPT (GUID Partition Table)",
        }
        return labels[self]

    def supports_bios(self) -> bool:
        """Return True if this scheme supports BIOS (legacy) boot."""
        return self == PartitionScheme.MBR

    def supports_uefi(self) -> bool:
        """Return True if this scheme supports UEFI boot."""
        return True
