"""About dialog — displays application version and license information."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from fluxdrive import __version__


class AboutDialog(QDialog):
    """Modal dialog displaying FluxDrive version and license information."""

    def __init__(self, parent: object = None) -> None:
        """Initialize the about dialog.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)  # type: ignore[call-arg]
        self.setWindowTitle("About FluxDrive")
        self.setMinimumWidth(360)
        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the about dialog layout."""
        layout = QVBoxLayout(self)

        title = QLabel(f"<b>FluxDrive</b> v{__version__}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; margin: 8px;")

        description = QLabel(
            "Linux alternative to Rufus for creating bootable USB drives.<br>"
            "Supports BIOS, UEFI, and hybrid ISOs."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)

        license_label = QLabel("License: GNU General Public License v3.0 or later")
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        license_label.setStyleSheet("color: #888; font-size: 11px;")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(license_label)
        layout.addWidget(buttons)
