"""Unit tests for domain value objects and IsoImage entity methods."""

import pytest

from fluxdrive.domain.entities.iso_image import IsoImage
from fluxdrive.domain.value_objects.cluster_size import ClusterSize
from fluxdrive.domain.value_objects.file_system import FileSystem
from fluxdrive.domain.value_objects.hash_algorithm import HashAlgorithm
from fluxdrive.domain.value_objects.partition_scheme import PartitionScheme
from fluxdrive.domain.value_objects.target_system import TargetSystem
from fluxdrive.domain.value_objects.write_mode import WriteMode


@pytest.mark.unit
class TestPartitionScheme:
    """Tests for PartitionScheme value object helpers."""

    def test_mbr_label_contains_text(self) -> None:
        """PartitionScheme.MBR.label() returns a non-empty string."""
        assert "MBR" in PartitionScheme.MBR.label()

    def test_gpt_label_contains_text(self) -> None:
        """PartitionScheme.GPT.label() returns a non-empty string."""
        assert "GPT" in PartitionScheme.GPT.label()

    def test_mbr_supports_bios(self) -> None:
        """MBR supports BIOS boot."""
        assert PartitionScheme.MBR.supports_bios() is True

    def test_gpt_does_not_support_bios(self) -> None:
        """GPT does not support BIOS boot."""
        assert PartitionScheme.GPT.supports_bios() is False

    def test_both_schemes_support_uefi(self) -> None:
        """Both MBR and GPT support UEFI boot."""
        assert PartitionScheme.MBR.supports_uefi() is True
        assert PartitionScheme.GPT.supports_uefi() is True


@pytest.mark.unit
class TestTargetSystem:
    """Tests for TargetSystem value object helpers."""

    def test_all_targets_have_labels(self) -> None:
        """Every TargetSystem variant returns a non-empty label string."""
        for target in TargetSystem:
            assert len(target.label()) > 0

    def test_bios_requires_bios_bootloader(self) -> None:
        """BIOS target requires a BIOS bootloader."""
        assert TargetSystem.BIOS.requires_bios_bootloader() is True

    def test_uefi_does_not_require_bios_bootloader(self) -> None:
        """UEFI-only target does not require a BIOS bootloader."""
        assert TargetSystem.UEFI.requires_bios_bootloader() is False

    def test_dual_requires_both_bootloaders(self) -> None:
        """Dual BIOS+UEFI target requires both bootloaders."""
        assert TargetSystem.BIOS_UEFI.requires_bios_bootloader() is True
        assert TargetSystem.BIOS_UEFI.requires_uefi_bootloader() is True

    def test_bios_does_not_require_uefi(self) -> None:
        """BIOS-only target does not require a UEFI bootloader."""
        assert TargetSystem.BIOS.requires_uefi_bootloader() is False


@pytest.mark.unit
class TestFileSystem:
    """Tests for FileSystem value object helpers."""

    def test_all_filesystems_have_labels(self) -> None:
        """Every FileSystem variant returns a non-empty label string."""
        for fs in FileSystem:
            assert len(fs.label()) > 0

    def test_all_filesystems_have_mkfs_command(self) -> None:
        """Every FileSystem variant returns a non-empty mkfs command."""
        for fs in FileSystem:
            assert fs.mkfs_command().startswith("mkfs")

    def test_ntfs_supports_large_files(self) -> None:
        """NTFS supports files larger than 4 GB."""
        assert FileSystem.NTFS.supports_large_files() is True

    def test_fat32_does_not_support_large_files(self) -> None:
        """Standard FAT32 does not support files >= 4 GB."""
        assert FileSystem.FAT32.supports_large_files() is False

    def test_fat32_is_uefi_compatible(self) -> None:
        """FAT32 is readable by UEFI firmware."""
        assert FileSystem.FAT32.is_uefi_compatible() is True

    def test_ext4_is_not_uefi_compatible(self) -> None:
        """ext4 is not natively readable by UEFI firmware."""
        assert FileSystem.EXT4.is_uefi_compatible() is False


@pytest.mark.unit
class TestClusterSize:
    """Tests for ClusterSize value object label formatting."""

    def test_default_label(self) -> None:
        """ClusterSize.DEFAULT label is 'Default'."""
        assert ClusterSize.DEFAULT.label() == "Default"

    def test_kilobyte_label(self) -> None:
        """Cluster sizes ≥ 1024 bytes are displayed in KB."""
        assert "KB" in ClusterSize.BYTES_4K.label()

    def test_byte_label(self) -> None:
        """Cluster sizes < 1024 bytes are displayed in bytes."""
        assert "bytes" in ClusterSize.BYTES_512.label()


@pytest.mark.unit
class TestHashAlgorithm:
    """Tests for HashAlgorithm value object helpers."""

    def test_all_algorithms_have_labels(self) -> None:
        """Every HashAlgorithm variant returns an uppercase label."""
        for algo in HashAlgorithm:
            assert algo.label() == algo.value.upper()

    def test_digest_lengths_are_correct(self) -> None:
        """HashAlgorithm.digest_length() returns the expected hex string length."""
        assert HashAlgorithm.MD5.digest_length() == 32
        assert HashAlgorithm.SHA1.digest_length() == 40
        assert HashAlgorithm.SHA256.digest_length() == 64
        assert HashAlgorithm.SHA512.digest_length() == 128


@pytest.mark.unit
class TestWriteMode:
    """Tests for WriteMode value object helpers."""

    def test_all_modes_have_labels(self) -> None:
        """Every WriteMode variant returns a non-empty label string."""
        for mode in WriteMode:
            assert len(mode.label()) > 0

    def test_iso_mode_allows_persistent_partition(self) -> None:
        """ISO_IMAGE mode allows adding a persistent partition."""
        assert WriteMode.ISO_IMAGE.allows_persistent_partition() is True

    def test_dd_mode_does_not_allow_persistent_partition(self) -> None:
        """DD_IMAGE mode does not allow adding a persistent partition."""
        assert WriteMode.DD_IMAGE.allows_persistent_partition() is False


@pytest.mark.unit
class TestIsoImage:
    """Tests for IsoImage entity methods not covered by conftest fixtures."""

    def test_size_gib_calculation(self, tmp_path: object) -> None:
        """size_gib() returns correct GiB value for a 1 GiB image."""
        from pathlib import Path

        assert isinstance(tmp_path, Path)
        iso = IsoImage(path=tmp_path / "x.iso", size_bytes=1024**3)
        assert iso.size_gib() == 1.0

    def test_size_label_gib(self, tmp_path: object) -> None:
        """size_label() includes 'GiB' for images >= 1 GiB."""
        from pathlib import Path

        assert isinstance(tmp_path, Path)
        iso = IsoImage(path=tmp_path / "x.iso", size_bytes=2 * 1024**3)
        assert "GiB" in iso.size_label()

    def test_size_label_mib(self, tmp_path: object) -> None:
        """size_label() includes 'MiB' for images < 1 GiB."""
        from pathlib import Path

        assert isinstance(tmp_path, Path)
        iso = IsoImage(path=tmp_path / "x.iso", size_bytes=512 * 1024**2)
        assert "MiB" in iso.size_label()

    def test_filename_returns_basename(self, tmp_path: object) -> None:
        """filename() returns only the file name without parent directories."""
        from pathlib import Path

        assert isinstance(tmp_path, Path)
        iso = IsoImage(path=tmp_path / "ubuntu-24.04.iso", size_bytes=100)
        assert iso.filename() == "ubuntu-24.04.iso"

    def test_is_img_true_for_img_extension(self, tmp_path: object) -> None:
        """is_img() returns True for .img files."""
        from pathlib import Path

        assert isinstance(tmp_path, Path)
        iso = IsoImage(path=tmp_path / "disk.img", size_bytes=100)
        assert iso.is_img() is True

    def test_is_img_false_for_iso_extension(self, tmp_path: object) -> None:
        """is_img() returns False for .iso files."""
        from pathlib import Path

        assert isinstance(tmp_path, Path)
        iso = IsoImage(path=tmp_path / "disk.iso", size_bytes=100)
        assert iso.is_img() is False
