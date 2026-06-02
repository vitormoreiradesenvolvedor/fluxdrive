"""Main window view model — mediates between UI and application use cases."""

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from fluxdrive.application.contracts.i_device_scanner import IDeviceScanner
from fluxdrive.application.contracts.i_downloader import DownloadableIso
from fluxdrive.application.use_cases.check_bad_blocks_use_case import CheckBadBlocksUseCase
from fluxdrive.application.use_cases.detect_iso_type_use_case import DetectIsoTypeUseCase
from fluxdrive.application.use_cases.download_iso_use_case import DownloadIsoUseCase
from fluxdrive.application.use_cases.format_drive_use_case import FormatDriveUseCase
from fluxdrive.application.use_cases.verify_hash_use_case import VerifyHashUseCase
from fluxdrive.application.use_cases.write_iso_use_case import WriteIsoUseCase
from fluxdrive.domain.entities.device import Device
from fluxdrive.domain.entities.iso_image import IsoImage
from fluxdrive.domain.entities.write_config import WriteConfig
from fluxdrive.domain.value_objects.hash_algorithm import HashAlgorithm


class _WriteWorker(QThread):
    """Background worker for long-running write operations.

    Runs in a separate thread to keep the UI responsive during
    potentially hour-long USB write operations.
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        use_case: WriteIsoUseCase,
        config: WriteConfig,
    ) -> None:
        """Initialize with the use case and configuration to execute.

        Args:
            use_case: The WriteIsoUseCase to execute.
            config: Write configuration passed to the use case.
        """
        super().__init__()
        self._use_case = use_case
        self._config = config

    def run(self) -> None:
        """Execute the write operation in a background thread."""
        try:
            self._use_case.execute(self._config, self.progress.emit)
            self.finished.emit()
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class MainViewModel(QObject):
    """View model for the main FluxDrive window.

    Owns all use case instances and exposes Qt signals for the UI
    to connect to, following the MVVM pattern. The UI layer has no
    direct dependency on use cases or domain objects.
    """

    devices_refreshed = pyqtSignal(list)
    iso_detected = pyqtSignal(object)
    write_progress = pyqtSignal(int, str)
    write_finished = pyqtSignal()
    write_error = pyqtSignal(str)
    hash_computed = pyqtSignal(str)
    hash_error = pyqtSignal(str)
    log_message = pyqtSignal(str)

    def __init__(
        self,
        device_scanner: IDeviceScanner,
        write_use_case: WriteIsoUseCase,
        format_use_case: FormatDriveUseCase,
        detect_use_case: DetectIsoTypeUseCase,
        hash_use_case: VerifyHashUseCase,
        download_use_case: DownloadIsoUseCase,
        bad_blocks_use_case: CheckBadBlocksUseCase,
    ) -> None:
        """Initialize with all required use cases (Dependency Injection).

        Args:
            device_scanner: IDeviceScanner implementation.
            write_use_case: WriteIsoUseCase instance.
            format_use_case: FormatDriveUseCase instance.
            detect_use_case: DetectIsoTypeUseCase instance.
            hash_use_case: VerifyHashUseCase instance.
            download_use_case: DownloadIsoUseCase instance.
            bad_blocks_use_case: CheckBadBlocksUseCase instance.
        """
        super().__init__()
        self._scanner = device_scanner
        self._write = write_use_case
        self._format = format_use_case
        self._detect = detect_use_case
        self._hash = hash_use_case
        self._download = download_use_case
        self._bad_blocks = bad_blocks_use_case
        self._worker: _WriteWorker | None = None

    def refresh_devices(self) -> list[Device]:
        """Scan for removable devices and emit the results.

        Returns:
            List of detected Device entities.
        """
        devices = self._scanner.list_removable_devices()
        self.devices_refreshed.emit(devices)
        self.log_message.emit(f"Found {len(devices)} device(s).")
        return devices

    def detect_iso(self, path: Path) -> IsoImage:
        """Detect the ISO type and emit the result.

        Args:
            path: Path to the ISO file.

        Returns:
            IsoImage entity with boot capabilities populated.
        """
        iso = self._detect.execute(path)
        self.iso_detected.emit(iso)
        self.log_message.emit(
            f"ISO detected: {iso.filename()} "
            f"({'hybrid' if iso.is_hybrid else 'BIOS' if iso.has_bios else 'UEFI'})"
        )
        return iso

    def start_write(self, config: WriteConfig) -> None:
        """Start the write operation in a background thread.

        Args:
            config: Complete write configuration.
        """
        self.log_message.emit(
            f"Starting write: {config.device.path} ← "
            f"{config.iso_image.filename() if config.iso_image else '(format only)'}"
        )
        self._worker = _WriteWorker(self._write, config)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def compute_hash(
        self,
        path: Path,
        algorithm: HashAlgorithm,
    ) -> None:
        """Compute the hash of an ISO file asynchronously.

        Args:
            path: Path to the ISO file.
            algorithm: Hash algorithm to use.
        """
        try:
            digest = self._hash.compute_hash(path, algorithm)
            self.hash_computed.emit(digest)
        except Exception as exc:  # noqa: BLE001
            self.hash_error.emit(str(exc))

    def list_downloadable_isos(self) -> list[DownloadableIso]:
        """Return the curated list of downloadable ISO images.

        Returns:
            List of DownloadableIso descriptors.
        """
        return self._download.list_sources()

    def _on_progress(self, percent: int, message: str) -> None:
        """Forward progress updates and append to log.

        Args:
            percent: Progress percentage (0–100).
            message: Status message for the log.
        """
        self.write_progress.emit(percent, message)
        if message:
            self.log_message.emit(message)

    def _on_finished(self) -> None:
        """Handle successful write completion."""
        self.write_finished.emit()
        self.log_message.emit("Write operation completed successfully.")

    def _on_error(self, message: str) -> None:
        """Handle write operation errors.

        Args:
            message: Error description.
        """
        self.write_error.emit(message)
        self.log_message.emit(f"ERROR: {message}")
