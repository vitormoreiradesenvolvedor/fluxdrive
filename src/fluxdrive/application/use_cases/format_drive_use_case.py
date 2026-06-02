"""Use case for formatting a drive without writing an ISO."""

from collections.abc import Callable

from fluxdrive.application.contracts.i_drive_formatter import IDriveFormatter
from fluxdrive.domain.entities.write_config import WriteConfig
from fluxdrive.domain.exceptions.device_errors import DeviceNotRemovableError


class FormatDriveUseCase:
    """Orchestrates a format-only operation on a USB device.

    Validates that the device is safe to format, then delegates
    partitioning and filesystem creation to the IDriveFormatter.
    """

    def __init__(self, formatter: IDriveFormatter) -> None:
        """Initialize with a concrete formatter implementation.

        Args:
            formatter: An IDriveFormatter implementation.
        """
        self._formatter = formatter

    def execute(
        self,
        config: WriteConfig,
        progress_callback: Callable[[int, str], None],
    ) -> None:
        """Format the device according to the supplied configuration.

        Args:
            config: Write configuration (iso_image must be None).
            progress_callback: Called with (percent: int, message: str).

        Raises:
            DeviceNotRemovableError: If the target device is not removable.
            PartitioningError: If partition table creation fails.
            FormatError: If filesystem creation fails.
        """
        if not config.device.is_removable:
            raise DeviceNotRemovableError(
                f"Device {config.device.path} is not removable."
            )
        self._formatter.format(config, progress_callback)
