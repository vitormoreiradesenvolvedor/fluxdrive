"""Unit tests for the WriteIsoUseCase."""

from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from fluxdrive.application.contracts.i_iso_writer import IIsoWriter
from fluxdrive.application.use_cases.write_iso_use_case import WriteIsoUseCase
from fluxdrive.domain.entities.device import Device
from fluxdrive.domain.entities.iso_image import IsoImage
from fluxdrive.domain.entities.write_config import WriteConfig
from fluxdrive.domain.exceptions.device_errors import (
    DeviceNotRemovableError,
    DeviceTooSmallError,
)
from fluxdrive.domain.exceptions.write_errors import IsoFileNotFoundError
from fluxdrive.domain.value_objects.file_system import FileSystem
from fluxdrive.domain.value_objects.partition_scheme import PartitionScheme
from fluxdrive.domain.value_objects.target_system import TargetSystem
from fluxdrive.domain.value_objects.write_mode import WriteMode


def _make_writer(handles: bool = True) -> MagicMock:
    """Create a mock IIsoWriter that optionally handles configs.

    Args:
        handles: Return value for can_handle().

    Returns:
        Configured MagicMock.
    """
    writer = MagicMock(spec=IIsoWriter)
    writer.can_handle.return_value = handles
    return writer


@pytest.mark.unit
class TestWriteIsoUseCase:
    """Tests for WriteIsoUseCase validation and writer selection."""

    def test_raises_when_device_not_removable(
        self, sample_iso: IsoImage, sample_device: Device
    ) -> None:
        """execute() raises DeviceNotRemovableError for non-removable devices."""
        non_removable = Device(
            path=sample_device.path,
            name="HDD",
            size_bytes=sample_device.size_bytes,
            is_removable=False,
        )
        config = WriteConfig(
            device=non_removable,
            iso_image=sample_iso,
            partition_scheme=PartitionScheme.MBR,
            target_system=TargetSystem.BIOS,
            file_system=FileSystem.FAT32,
        )
        use_case = WriteIsoUseCase(writers=[_make_writer()])

        with pytest.raises(DeviceNotRemovableError):
            use_case.execute(config, lambda p, m: None)

    def test_raises_when_device_too_small(self, sample_device: Device, tmp_path: Path) -> None:
        """execute() raises DeviceTooSmallError when device is smaller than ISO."""
        large_iso_file = tmp_path / "large.iso"
        large_iso_file.write_bytes(b"\x00" * 100)
        large_iso = IsoImage(
            path=large_iso_file,
            size_bytes=sample_device.size_bytes + 1,
        )
        config = WriteConfig(
            device=sample_device,
            iso_image=large_iso,
            partition_scheme=PartitionScheme.MBR,
            target_system=TargetSystem.BIOS,
            file_system=FileSystem.FAT32,
        )
        use_case = WriteIsoUseCase(writers=[_make_writer()])

        with pytest.raises(DeviceTooSmallError):
            use_case.execute(config, lambda p, m: None)

    def test_raises_when_iso_file_missing(self, sample_device: Device) -> None:
        """execute() raises IsoFileNotFoundError when ISO path doesn't exist."""
        missing_iso = IsoImage(
            path=Path("/nonexistent/path/test.iso"),
            size_bytes=100,
        )
        config = WriteConfig(
            device=sample_device,
            iso_image=missing_iso,
            partition_scheme=PartitionScheme.MBR,
            target_system=TargetSystem.BIOS,
            file_system=FileSystem.FAT32,
        )
        use_case = WriteIsoUseCase(writers=[_make_writer()])

        with pytest.raises(IsoFileNotFoundError):
            use_case.execute(config, lambda p, m: None)

    def test_selects_correct_writer(self, sample_write_config: WriteConfig) -> None:
        """execute() calls write() on the first writer that can_handle() returns True."""
        non_handler = _make_writer(handles=False)
        handler = _make_writer(handles=True)
        use_case = WriteIsoUseCase(writers=[non_handler, handler])

        use_case.execute(sample_write_config, lambda p, m: None)

        handler.write.assert_called_once()
        non_handler.write.assert_not_called()

    def test_raises_when_no_writer_available(self, sample_write_config: WriteConfig) -> None:
        """execute() raises RuntimeError when no writer handles the config."""
        non_handler = _make_writer(handles=False)
        use_case = WriteIsoUseCase(writers=[non_handler])

        with pytest.raises(RuntimeError, match="No writer available"):
            use_case.execute(sample_write_config, lambda p, m: None)
