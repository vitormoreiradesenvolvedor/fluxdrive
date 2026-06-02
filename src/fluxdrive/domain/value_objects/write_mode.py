"""Write mode value object — determines how the ISO is written to the device."""

from enum import Enum, unique


@unique
class WriteMode(str, Enum):
    """USB write modes.

    ISO_IMAGE extracts ISO contents and installs a bootloader — allows
    adding extra files and creating a persistent partition afterwards.

    DD_IMAGE writes the ISO byte-for-byte using dd — preserves the exact
    ISO structure but does not allow modification after writing.
    """

    ISO_IMAGE = "iso"
    DD_IMAGE = "dd"

    def label(self) -> str:
        """Return a human-readable label for display in the UI."""
        labels = {
            WriteMode.ISO_IMAGE: "ISO Image mode (recommended)",
            WriteMode.DD_IMAGE: "DD Image mode (byte-for-byte copy)",
        }
        return labels[self]

    def allows_persistent_partition(self) -> bool:
        """Return True if a persistent partition can be added after writing."""
        return self == WriteMode.ISO_IMAGE
