"""Shared fixtures for the FluxDrive test suite."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fluxdrive.domain.entities.device import Device
from fluxdrive.domain.entities.iso_image import IsoImage
from fluxdrive.domain.entities.write_config import WriteConfig
from fluxdrive.domain.value_objects.cluster_size import ClusterSize
from fluxdrive.domain.value_objects.file_system import FileSystem
from fluxdrive.domain.value_objects.partition_scheme import PartitionScheme
from fluxdrive.domain.value_objects.target_system import TargetSystem
from fluxdrive.domain.value_objects.write_mode import WriteMode


@pytest.fixture
def sample_device() -> Device:
    """Return a minimal removable device fixture.

    Returns:
        Device entity representing a 16 GiB removable USB drive.
    """
    return Device(
        path=Path("/dev/sdb"),
        name="TestUSB",
        size_bytes=16 * 1024**3,
        is_removable=True,
        vendor="TestVendor",
        model="TestModel",
        partitions=("/dev/sdb1",),
    )


@pytest.fixture
def sample_iso(tmp_path: Path) -> IsoImage:
    """Create a minimal ISO file fixture for testing.

    Returns:
        IsoImage pointing to a temporary file with BIOS+UEFI flags set.
    """
    iso_file = tmp_path / "test.iso"
    iso_file.write_bytes(b"\x00" * 1024)
    return IsoImage(
        path=iso_file,
        size_bytes=1024,
        is_hybrid=True,
        has_uefi=True,
        has_bios=True,
        label="TESTISO",
    )


@pytest.fixture
def sample_write_config(sample_device: Device, sample_iso: IsoImage) -> WriteConfig:
    """Return a complete write configuration fixture.

    Args:
        sample_device: Injected Device fixture.
        sample_iso: Injected IsoImage fixture.

    Returns:
        WriteConfig with default options and ISO mode.
    """
    return WriteConfig(
        device=sample_device,
        iso_image=sample_iso,
        partition_scheme=PartitionScheme.MBR,
        target_system=TargetSystem.BIOS_UEFI,
        file_system=FileSystem.FAT32,
        cluster_size=ClusterSize.DEFAULT,
        volume_label="TESTDRIVE",
        write_mode=WriteMode.ISO_IMAGE,
    )


@pytest.fixture
def mock_device_scanner() -> MagicMock:
    """Return a mock IDeviceScanner.

    Returns:
        MagicMock configured as an IDeviceScanner.
    """
    from fluxdrive.application.contracts.i_device_scanner import IDeviceScanner

    return MagicMock(spec=IDeviceScanner)


@pytest.fixture
def mock_hash_verifier() -> MagicMock:
    """Return a mock IHashVerifier.

    Returns:
        MagicMock configured as an IHashVerifier.
    """
    from fluxdrive.application.contracts.i_hash_verifier import IHashVerifier

    return MagicMock(spec=IHashVerifier)
