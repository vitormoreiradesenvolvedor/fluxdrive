"""Interface for ISO boot type detection."""

from abc import ABC, abstractmethod
from pathlib import Path

from fluxdrive.domain.entities.iso_image import IsoImage


class IIsoDetector(ABC):
    """Contract for analysing an ISO file and determining its boot capabilities."""

    @abstractmethod
    def detect(self, path: Path) -> IsoImage:
        """Analyse an ISO/IMG file and return a populated IsoImage entity.

        Reads the ISO headers to determine:
        - Whether it contains BIOS boot sectors.
        - Whether it contains an EFI System Partition or UEFI boot loader.
        - Whether it is a hybrid ISO (supports both BIOS and UEFI).
        - The volume label from the ISO filesystem.

        Args:
            path: Absolute path to the ISO or IMG file.

        Returns:
            An IsoImage entity with boot capability flags populated.

        Raises:
            IsoFileNotFoundError: If the file does not exist.
        """
