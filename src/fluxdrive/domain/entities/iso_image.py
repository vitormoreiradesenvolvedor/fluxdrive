"""ISO image entity — represents a local ISO or IMG file to be written."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IsoImage:
    """An immutable descriptor of an ISO/IMG file on the local filesystem.

    Attributes:
        path: Absolute path to the ISO file.
        size_bytes: File size in bytes.
        is_hybrid: True when the ISO contains both BIOS and UEFI boot sectors.
        has_uefi: True when the ISO contains an EFI boot partition or loader.
        has_bios: True when the ISO contains a BIOS bootable section.
        label: Volume label read from the ISO filesystem, if any.
    """

    path: Path
    size_bytes: int
    is_hybrid: bool = False
    has_uefi: bool = False
    has_bios: bool = False
    label: str = ""

    def size_gib(self) -> float:
        """Return file size in gibibytes, rounded to two decimal places."""
        return round(self.size_bytes / (1024**3), 2)

    def size_label(self) -> str:
        """Return a formatted human-readable size string."""
        gib = self.size_gib()
        if gib >= 1.0:
            return f"{gib:.2f} GiB"
        mib = round(self.size_bytes / (1024**2), 1)
        return f"{mib:.1f} MiB"

    def filename(self) -> str:
        """Return just the filename portion of the path."""
        return self.path.name

    def is_img(self) -> bool:
        """Return True if the file has a .img extension."""
        return self.path.suffix.lower() == ".img"
