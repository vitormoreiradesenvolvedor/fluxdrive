"""Use case registry — groups all application use cases into a single value object."""

from dataclasses import dataclass

from fluxdrive.application.use_cases.check_bad_blocks_use_case import CheckBadBlocksUseCase
from fluxdrive.application.use_cases.detect_iso_type_use_case import DetectIsoTypeUseCase
from fluxdrive.application.use_cases.download_iso_use_case import DownloadIsoUseCase
from fluxdrive.application.use_cases.format_drive_use_case import FormatDriveUseCase
from fluxdrive.application.use_cases.verify_hash_use_case import VerifyHashUseCase
from fluxdrive.application.use_cases.write_iso_use_case import WriteIsoUseCase


@dataclass(frozen=True)
class UseCaseRegistry:
    """Immutable container for all application use cases.

    Groups the six use cases so that MainViewModel can accept a single
    dependency instead of six separate constructor parameters, keeping
    its parameter count within the Clean Code limit.

    Attributes:
        write: Use case for writing an ISO image to a device.
        format: Use case for formatting a device without writing.
        detect: Use case for detecting ISO boot capabilities.
        hash: Use case for computing and verifying file hashes.
        download: Use case for downloading curated ISO images.
        bad_blocks: Use case for checking a device for bad blocks.
    """

    write: WriteIsoUseCase
    format: FormatDriveUseCase
    detect: DetectIsoTypeUseCase
    hash: VerifyHashUseCase
    download: DownloadIsoUseCase
    bad_blocks: CheckBadBlocksUseCase
