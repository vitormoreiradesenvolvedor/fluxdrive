"""Use case for writing an ISO image to a USB device."""

from collections.abc import Callable

from fluxdrive.application.contracts.i_iso_writer import IIsoWriter
from fluxdrive.domain.entities.write_config import WriteConfig
from fluxdrive.domain.exceptions.device_errors import (
    DeviceNotRemovableError,
    DeviceTooSmallError,
)
from fluxdrive.domain.exceptions.write_errors import IsoFileNotFoundError


class WriteIsoUseCase:
    """Orchestrates writing an ISO image to a USB device.

    Validates preconditions before delegating to the appropriate
    IIsoWriter strategy, ensuring the operation is safe to proceed.
    """

    def __init__(self, writers: list[IIsoWriter]) -> None:
        """Initialize with a list of available writer strategies.

        Args:
            writers: All available IIsoWriter implementations. The use case
                     selects the appropriate one via can_handle().
        """
        self._writers = writers

    def execute(
        self,
        config: WriteConfig,
        progress_callback: Callable[[int, str], None],
    ) -> None:
        """Validate the config and write the ISO to the target device.

        Args:
            config: Write configuration with device, ISO, and options.
            progress_callback: Called with (percent: int, message: str).

        Raises:
            DeviceNotRemovableError: If the target device is not removable.
            DeviceTooSmallError: If the device is smaller than the ISO.
            IsoFileNotFoundError: If the ISO file does not exist.
            WriteError: If no compatible writer is found or write fails.
        """
        self._validate(config)
        writer = self._select_writer(config)
        writer.write(config, progress_callback)

    def _validate(self, config: WriteConfig) -> None:
        """Validate preconditions before starting the write.

        Args:
            config: The configuration to validate.
        """
        if not config.device.is_removable:
            raise DeviceNotRemovableError(
                f"Device {config.device.path} is not marked as removable."
            )

        if config.iso_image is not None:
            if not config.iso_image.path.exists():
                raise IsoFileNotFoundError(
                    f"ISO file not found: {config.iso_image.path}"
                )
            if not config.device.is_large_enough_for(config.iso_image.size_bytes):
                raise DeviceTooSmallError(
                    config.device.size_bytes, config.iso_image.size_bytes
                )

    def _select_writer(self, config: WriteConfig) -> IIsoWriter:
        """Return the first writer that can handle the given config.

        Args:
            config: The write configuration to match.

        Raises:
            RuntimeError: If no registered writer supports this configuration.
        """
        for writer in self._writers:
            if writer.can_handle(config):
                return writer
        raise RuntimeError(
            f"No writer available for write mode: {config.write_mode}"
        )
