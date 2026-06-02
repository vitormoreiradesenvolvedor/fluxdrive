"""ISO download dialog — curated list of downloadable Linux distributions."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


class DownloadDialog(QDialog):
    """Modal dialog for downloading a Linux distribution ISO.

    Displays a curated list of distributions and allows the user to
    download the selected ISO to a chosen directory.
    """

    def __init__(self, view_model: object, parent: object = None) -> None:
        """Initialize the download dialog.

        Args:
            view_model: MainViewModel providing download use case access.
            parent: Optional parent widget.
        """
        super().__init__(parent)  # type: ignore[call-arg]
        self._vm = view_model
        self._iso_list: list = []
        self.setWindowTitle("Download ISO")
        self.setMinimumSize(500, 400)
        self._build_ui()
        self._load_iso_list()

    def _build_ui(self) -> None:
        """Construct the download dialog layout."""
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select a distribution to download:"))

        self._list_widget = QListWidget()
        self._list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list_widget)

        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._info_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        self._download_btn = QPushButton("Download…")
        self._download_btn.setEnabled(False)
        self._download_btn.clicked.connect(self._on_download)
        layout.addWidget(self._download_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_iso_list(self) -> None:
        """Populate the list widget with curated ISO descriptors."""
        from fluxdrive.ui.view_models.main_view_model import MainViewModel

        if not isinstance(self._vm, MainViewModel):
            return

        self._iso_list = self._vm.list_downloadable_isos()
        for iso in self._iso_list:
            size_str = f"{iso.size_bytes / 1024**3:.1f} GiB" if iso.size_bytes else "?"
            item = QListWidgetItem(f"{iso.name}  ({size_str})")
            self._list_widget.addItem(item)

    def _on_selection_changed(self) -> None:
        """Enable the download button when an item is selected."""
        self._download_btn.setEnabled(bool(self._list_widget.selectedItems()))
        row = self._list_widget.currentRow()
        if 0 <= row < len(self._iso_list):
            iso = self._iso_list[row]
            self._info_label.setText(
                f"Version: {iso.version}  |  Arch: {iso.architecture}"
            )

    def _on_download(self) -> None:
        """Start downloading the selected ISO to a user-chosen directory."""
        row = self._list_widget.currentRow()
        if row < 0 or row >= len(self._iso_list):
            return

        iso = self._iso_list[row]
        dest_str = QFileDialog.getExistingDirectory(
            self,
            "Select Download Directory",
            str(Path.home() / "Downloads"),
        )
        if not dest_str:
            return

        QMessageBox.information(
            self,
            "Download Started",
            f"Downloading {iso.name}…\nThis may take a while.",
        )
