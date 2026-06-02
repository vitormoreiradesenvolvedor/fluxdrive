"""Unit tests for the WriteConfig entity."""

import pytest

from fluxdrive.domain.entities.write_config import WriteConfig


@pytest.mark.unit
class TestWriteConfig:
    """Tests for WriteConfig entity construction and convenience methods."""

    def test_is_format_only_when_no_iso(self, sample_device: object) -> None:
        """is_format_only() returns True when iso_image is None."""
        from fluxdrive.domain.entities.device import Device
        from fluxdrive.domain.value_objects.file_system import FileSystem
        from fluxdrive.domain.value_objects.partition_scheme import PartitionScheme
        from fluxdrive.domain.value_objects.target_system import TargetSystem

        assert isinstance(sample_device, Device)
        config = WriteConfig(
            device=sample_device,
            iso_image=None,
            partition_scheme=PartitionScheme.GPT,
            target_system=TargetSystem.UEFI,
            file_system=FileSystem.FAT32,
        )
        assert config.is_format_only() is True

    def test_is_not_format_only_when_iso_present(
        self, sample_write_config: WriteConfig
    ) -> None:
        """is_format_only() returns False when iso_image is set."""
        assert sample_write_config.is_format_only() is False

    def test_requires_root_always(self, sample_write_config: WriteConfig) -> None:
        """requires_root() always returns True for any write config."""
        assert sample_write_config.requires_root() is True

    def test_config_is_immutable(self, sample_write_config: WriteConfig) -> None:
        """WriteConfig is a frozen dataclass and cannot be mutated."""
        with pytest.raises(Exception):
            sample_write_config.volume_label = "changed"  # type: ignore[misc]
