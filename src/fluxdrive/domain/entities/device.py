"""Device entity — represents a physical storage device detected by the OS."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Device:
    """An immutable snapshot of a storage device's properties.

    This entity represents a removable drive detected by the system.
    It is intentionally immutable — device state is re-read from the OS
    each time the user refreshes the device list.

    Attributes:
        path: Block device path (e.g. /dev/sdb).
        name: Human-readable model name from the OS.
        size_bytes: Total device capacity in bytes.
        is_removable: True if the OS marks this device as removable.
        vendor: Device vendor string, empty when unavailable.
        model: Device model string, empty when unavailable.
        partitions: List of partition device paths (e.g. ['/dev/sdb1']).
    """

    path: Path
    name: str
    size_bytes: int
    is_removable: bool
    vendor: str = ""
    model: str = ""
    partitions: tuple[str, ...] = field(default_factory=tuple)

    def size_gib(self) -> float:
        """Return capacity in gibibytes (GiB), rounded to two decimal places."""
        return round(self.size_bytes / (1024**3), 2)

    def size_label(self) -> str:
        """Return a formatted human-readable capacity string (e.g. '7.45 GiB')."""
        gib = self.size_gib()
        if gib >= 1.0:
            return f"{gib:.2f} GiB"
        mib = round(self.size_bytes / (1024**2), 1)
        return f"{mib:.1f} MiB"

    def display_name(self) -> str:
        """Return a full display string suitable for the device selector combo box."""
        label = self.name or f"{self.vendor} {self.model}".strip() or str(self.path)
        return f"{label} [{self.size_label()}] ({self.path})"

    def is_large_enough_for(self, required_bytes: int) -> bool:
        """Return True if the device has at least the required capacity."""
        return self.size_bytes >= required_bytes
