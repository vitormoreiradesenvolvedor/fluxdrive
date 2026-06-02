"""Unit tests for the Device entity."""

from pathlib import Path

import pytest

from fluxdrive.domain.entities.device import Device


@pytest.mark.unit
class TestDevice:
    """Tests for Device entity behaviour and display formatting."""

    def test_size_gib_returns_correct_value(self) -> None:
        """Device.size_gib() returns the correct GiB value."""
        device = Device(
            path=Path("/dev/sdb"),
            name="Test",
            size_bytes=8 * 1024**3,
            is_removable=True,
        )
        assert device.size_gib() == 8.0

    def test_size_label_shows_gib_for_large_drives(self) -> None:
        """size_label() returns GiB string for drives >= 1 GiB."""
        device = Device(
            path=Path("/dev/sdb"),
            name="Test",
            size_bytes=16 * 1024**3,
            is_removable=True,
        )
        assert "GiB" in device.size_label()

    def test_size_label_shows_mib_for_small_drives(self) -> None:
        """size_label() returns MiB string for drives < 1 GiB."""
        device = Device(
            path=Path("/dev/sdb"),
            name="Test",
            size_bytes=512 * 1024**2,
            is_removable=True,
        )
        assert "MiB" in device.size_label()

    def test_display_name_includes_path_and_size(self) -> None:
        """display_name() includes both device path and size."""
        device = Device(
            path=Path("/dev/sdb"),
            name="MyDrive",
            size_bytes=8 * 1024**3,
            is_removable=True,
        )
        name = device.display_name()
        assert "/dev/sdb" in name
        assert "GiB" in name

    def test_is_large_enough_true_when_sufficient(self) -> None:
        """is_large_enough_for() returns True when device has enough space."""
        device = Device(
            path=Path("/dev/sdb"),
            name="Big",
            size_bytes=16 * 1024**3,
            is_removable=True,
        )
        assert device.is_large_enough_for(8 * 1024**3) is True

    def test_is_large_enough_false_when_insufficient(self) -> None:
        """is_large_enough_for() returns False when device is too small."""
        device = Device(
            path=Path("/dev/sdb"),
            name="Small",
            size_bytes=1 * 1024**3,
            is_removable=True,
        )
        assert device.is_large_enough_for(8 * 1024**3) is False

    def test_device_is_immutable(self) -> None:
        """Device is a frozen dataclass and cannot be mutated."""
        device = Device(
            path=Path("/dev/sdb"),
            name="Test",
            size_bytes=8 * 1024**3,
            is_removable=True,
        )
        with pytest.raises(Exception):
            device.name = "modified"  # type: ignore[misc]
