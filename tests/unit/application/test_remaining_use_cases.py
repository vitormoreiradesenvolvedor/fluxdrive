"""Unit tests for use cases not yet covered: detect, format, download, bad-blocks, registry."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fluxdrive.application.contracts.i_block_checker import IBlockChecker
from fluxdrive.application.contracts.i_downloader import DownloadableIso, IDownloader
from fluxdrive.application.contracts.i_drive_formatter import IDriveFormatter
from fluxdrive.application.contracts.i_iso_detector import IIsoDetector
from fluxdrive.application.use_cases.check_bad_blocks_use_case import CheckBadBlocksUseCase
from fluxdrive.application.use_cases.detect_iso_type_use_case import DetectIsoTypeUseCase
from fluxdrive.application.use_cases.download_iso_use_case import DownloadIsoUseCase
from fluxdrive.application.use_cases.format_drive_use_case import FormatDriveUseCase
from fluxdrive.application.use_cases.use_case_registry import UseCaseRegistry
from fluxdrive.application.use_cases.verify_hash_use_case import VerifyHashUseCase
from fluxdrive.application.use_cases.write_iso_use_case import WriteIsoUseCase
from fluxdrive.domain.entities.iso_image import IsoImage
from fluxdrive.domain.exceptions.device_errors import DeviceNotRemovableError


@pytest.mark.unit
class TestUseCaseRegistry:
    """Tests for UseCaseRegistry construction and attribute access."""

    def test_registry_exposes_all_use_cases(self) -> None:
        """UseCaseRegistry stores and exposes each use case by attribute name."""
        write = MagicMock(spec=WriteIsoUseCase)
        fmt = MagicMock(spec=FormatDriveUseCase)
        detect = MagicMock(spec=DetectIsoTypeUseCase)
        hsh = MagicMock(spec=VerifyHashUseCase)
        download = MagicMock(spec=DownloadIsoUseCase)
        blocks = MagicMock(spec=CheckBadBlocksUseCase)

        registry = UseCaseRegistry(
            write=write,
            format=fmt,
            detect=detect,
            hash=hsh,
            download=download,
            bad_blocks=blocks,
        )

        assert registry.write is write
        assert registry.format is fmt
        assert registry.detect is detect
        assert registry.hash is hsh
        assert registry.download is download
        assert registry.bad_blocks is blocks

    def test_registry_is_immutable(self) -> None:
        """UseCaseRegistry is a frozen dataclass and cannot be mutated."""
        registry = UseCaseRegistry(
            write=MagicMock(spec=WriteIsoUseCase),
            format=MagicMock(spec=FormatDriveUseCase),
            detect=MagicMock(spec=DetectIsoTypeUseCase),
            hash=MagicMock(spec=VerifyHashUseCase),
            download=MagicMock(spec=DownloadIsoUseCase),
            bad_blocks=MagicMock(spec=CheckBadBlocksUseCase),
        )
        with pytest.raises(Exception):
            registry.write = MagicMock()  # type: ignore[misc]


@pytest.mark.unit
class TestDetectIsoTypeUseCase:
    """Tests for DetectIsoTypeUseCase delegation."""

    def test_execute_delegates_to_detector(self, tmp_path: Path) -> None:
        """execute() returns the IsoImage from the injected detector."""
        iso_file = tmp_path / "test.iso"
        iso_file.write_bytes(b"\x00" * 16)
        expected = IsoImage(path=iso_file, size_bytes=16, has_bios=True)

        detector = MagicMock(spec=IIsoDetector)
        detector.detect.return_value = expected

        use_case = DetectIsoTypeUseCase(detector=detector)
        result = use_case.execute(iso_file)

        detector.detect.assert_called_once_with(iso_file)
        assert result is expected

    def test_execute_propagates_detector_exception(self, tmp_path: Path) -> None:
        """execute() lets exceptions from the detector propagate unchanged."""
        detector = MagicMock(spec=IIsoDetector)
        detector.detect.side_effect = FileNotFoundError("not found")

        use_case = DetectIsoTypeUseCase(detector=detector)
        with pytest.raises(FileNotFoundError):
            use_case.execute(tmp_path / "missing.iso")


@pytest.mark.unit
class TestFormatDriveUseCase:
    """Tests for FormatDriveUseCase validation and delegation."""

    def test_execute_calls_formatter(self, sample_write_config: object) -> None:
        """execute() delegates to the formatter when device is removable."""
        formatter = MagicMock(spec=IDriveFormatter)
        use_case = FormatDriveUseCase(formatter=formatter)
        use_case.execute(sample_write_config, lambda p, m: None)  # type: ignore[arg-type]
        formatter.format.assert_called_once()

    def test_execute_raises_for_non_removable(self, sample_write_config: object) -> None:
        """execute() raises DeviceNotRemovableError for non-removable devices."""
        from fluxdrive.domain.entities.device import Device
        from fluxdrive.domain.entities.write_config import WriteConfig
        from fluxdrive.domain.value_objects.file_system import FileSystem
        from fluxdrive.domain.value_objects.partition_scheme import PartitionScheme
        from fluxdrive.domain.value_objects.target_system import TargetSystem

        assert isinstance(sample_write_config, WriteConfig)
        non_removable = Device(
            path=sample_write_config.device.path,
            name="HDD",
            size_bytes=1024,
            is_removable=False,
        )
        config = WriteConfig(
            device=non_removable,
            iso_image=None,
            partition_scheme=PartitionScheme.GPT,
            target_system=TargetSystem.UEFI,
            file_system=FileSystem.FAT32,
        )
        use_case = FormatDriveUseCase(formatter=MagicMock(spec=IDriveFormatter))
        with pytest.raises(DeviceNotRemovableError):
            use_case.execute(config, lambda p, m: None)


@pytest.mark.unit
class TestDownloadIsoUseCase:
    """Tests for DownloadIsoUseCase delegation to IDownloader."""

    def _make_iso(self) -> DownloadableIso:
        """Return a minimal DownloadableIso fixture.

        Returns:
            A DownloadableIso with placeholder values.
        """
        return DownloadableIso(
            name="Test Linux 1.0",
            url="https://example.com/test.iso",
            size_bytes=1024,
            sha256="",
            version="1.0",
            architecture="amd64",
        )

    def test_list_sources_delegates_to_downloader(self) -> None:
        """list_sources() returns whatever the downloader provides."""
        iso = self._make_iso()
        downloader = MagicMock(spec=IDownloader)
        downloader.list_available.return_value = [iso]

        use_case = DownloadIsoUseCase(downloader=downloader)
        result = use_case.list_sources()

        assert result == [iso]
        downloader.list_available.assert_called_once()

    def test_download_delegates_to_downloader(self, tmp_path: Path) -> None:
        """download() returns the path provided by the downloader."""
        iso = self._make_iso()
        expected_path = tmp_path / "test.iso"

        downloader = MagicMock(spec=IDownloader)
        downloader.download.return_value = expected_path

        use_case = DownloadIsoUseCase(downloader=downloader)
        result = use_case.download(iso, tmp_path, lambda d, t, s: None)

        assert result == expected_path
        downloader.download.assert_called_once()


@pytest.mark.unit
class TestCheckBadBlocksUseCase:
    """Tests for CheckBadBlocksUseCase validation and delegation."""

    def test_execute_delegates_to_checker(self, tmp_path: Path) -> None:
        """execute() calls the checker and returns its bad-block count."""
        checker = MagicMock(spec=IBlockChecker)
        checker.check.return_value = 0

        use_case = CheckBadBlocksUseCase(checker=checker)
        result = use_case.execute(
            tmp_path / "dev", passes=1, progress_callback=lambda c, b, m: None
        )

        assert result == 0
        checker.check.assert_called_once()

    def test_execute_raises_for_invalid_passes(self, tmp_path: Path) -> None:
        """execute() raises ValueError when passes is outside the 1–4 range."""
        use_case = CheckBadBlocksUseCase(checker=MagicMock(spec=IBlockChecker))
        with pytest.raises(ValueError, match="passes must be between"):
            use_case.execute(tmp_path / "dev", passes=5, progress_callback=lambda c, b, m: None)

    def test_execute_rejects_zero_passes(self, tmp_path: Path) -> None:
        """execute() raises ValueError for zero passes."""
        use_case = CheckBadBlocksUseCase(checker=MagicMock(spec=IBlockChecker))
        with pytest.raises(ValueError):
            use_case.execute(tmp_path / "dev", passes=0, progress_callback=lambda c, b, m: None)
