"""Use case for detecting the boot type of an ISO file."""

from pathlib import Path

from fluxdrive.application.contracts.i_iso_detector import IIsoDetector
from fluxdrive.domain.entities.iso_image import IsoImage


class DetectIsoTypeUseCase:
    """Analyses an ISO/IMG file to determine its boot capabilities.

    Delegates file analysis to the injected IIsoDetector, keeping
    this use case free of I/O implementation details.
    """

    def __init__(self, detector: IIsoDetector) -> None:
        """Initialize with a concrete ISO detector implementation.

        Args:
            detector: An IIsoDetector implementation.
        """
        self._detector = detector

    def execute(self, path: Path) -> IsoImage:
        """Detect and return boot capabilities of the ISO at the given path.

        Args:
            path: Absolute path to the ISO or IMG file.

        Returns:
            IsoImage entity with has_bios, has_uefi, is_hybrid, and label populated.

        Raises:
            IsoFileNotFoundError: If the file does not exist.
        """
        return self._detector.detect(path)
