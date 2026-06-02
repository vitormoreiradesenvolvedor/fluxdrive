"""Target system value object — defines the target boot firmware."""

from enum import Enum, unique


@unique
class TargetSystem(str, Enum):
    """Boot firmware target for the bootable USB.

    Determines which bootloader chain will be installed on the device.
    BIOS_UEFI installs both bootloaders for maximum compatibility.
    """

    BIOS = "BIOS"
    UEFI = "UEFI"
    BIOS_UEFI = "BIOS_UEFI"

    def label(self) -> str:
        """Return a human-readable label for display in the UI."""
        labels = {
            TargetSystem.BIOS: "BIOS (or UEFI-CSM)",
            TargetSystem.UEFI: "UEFI (non CSM)",
            TargetSystem.BIOS_UEFI: "BIOS + UEFI (Dual boot)",
        }
        return labels[self]

    def requires_bios_bootloader(self) -> bool:
        """Return True if a BIOS-compatible bootloader must be installed."""
        return self in (TargetSystem.BIOS, TargetSystem.BIOS_UEFI)

    def requires_uefi_bootloader(self) -> bool:
        """Return True if a UEFI bootloader must be present."""
        return self in (TargetSystem.UEFI, TargetSystem.BIOS_UEFI)
