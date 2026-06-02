"""FluxDrive application entry point — wires dependencies and starts the UI."""

import os
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from fluxdrive.application.use_cases.check_bad_blocks_use_case import CheckBadBlocksUseCase
from fluxdrive.application.use_cases.detect_iso_type_use_case import DetectIsoTypeUseCase
from fluxdrive.application.use_cases.download_iso_use_case import DownloadIsoUseCase
from fluxdrive.application.use_cases.format_drive_use_case import FormatDriveUseCase
from fluxdrive.application.use_cases.use_case_registry import UseCaseRegistry
from fluxdrive.application.use_cases.verify_hash_use_case import VerifyHashUseCase
from fluxdrive.application.use_cases.write_iso_use_case import WriteIsoUseCase
from fluxdrive.infrastructure.block_checker import BadBlockChecker
from fluxdrive.infrastructure.device_scanner_udev import UdevDeviceScanner
from fluxdrive.infrastructure.downloader_requests import RequestsDownloader
from fluxdrive.infrastructure.drive_formatter import DriveFormatter
from fluxdrive.infrastructure.hash_verifier import HashlibHashVerifier
from fluxdrive.infrastructure.iso_detector import IsoDetector
from fluxdrive.infrastructure.iso_writer_dd import DdIsoWriter
from fluxdrive.infrastructure.iso_writer_iso import IsoModeWriter
from fluxdrive.ui.main_window import MainWindow
from fluxdrive.ui.view_models.main_view_model import MainViewModel


def _check_root() -> bool:
    """Return True if the process is running as root.

    Write operations require root privileges to access block devices.
    """
    return not os.geteuid()


def _compose_view_model() -> MainViewModel:
    """Compose all application dependencies (Composition Root).

    This function is the single place where concrete implementations
    are wired to their interfaces — the only place that imports both
    domain contracts and infrastructure adapters.

    Returns:
        A fully wired MainViewModel instance.
    """
    device_scanner = UdevDeviceScanner()
    formatter = DriveFormatter()
    hash_verifier = HashlibHashVerifier()
    iso_detector = IsoDetector()
    downloader = RequestsDownloader()
    block_checker = BadBlockChecker()

    writers = [IsoModeWriter(), DdIsoWriter()]

    use_cases = UseCaseRegistry(
        write=WriteIsoUseCase(writers=writers),
        format=FormatDriveUseCase(formatter=formatter),
        detect=DetectIsoTypeUseCase(detector=iso_detector),
        hash=VerifyHashUseCase(verifier=hash_verifier),
        download=DownloadIsoUseCase(downloader=downloader),
        bad_blocks=CheckBadBlocksUseCase(checker=block_checker),
    )

    return MainViewModel(
        device_scanner=device_scanner,
        use_cases=use_cases,
    )


def main() -> None:
    """Start the FluxDrive application.

    Checks for root privileges, composes the dependency graph,
    and launches the Qt event loop.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("FluxDrive")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("FluxDrive")

    if not _check_root():
        QMessageBox.warning(
            None,
            "Root Required",
            "FluxDrive requires root privileges to write to block devices.\n\n"
            "Please restart with: sudo fluxdrive",
        )

    view_model = _compose_view_model()
    window = MainWindow(view_model=view_model)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
