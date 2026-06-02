"""Main application window — FluxDrive's primary user interface."""

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from fluxdrive.domain.entities.device import Device
from fluxdrive.domain.entities.iso_image import IsoImage
from fluxdrive.domain.entities.write_config import WriteConfig
from fluxdrive.domain.value_objects.cluster_size import ClusterSize
from fluxdrive.domain.value_objects.file_system import FileSystem
from fluxdrive.domain.value_objects.partition_scheme import PartitionScheme
from fluxdrive.domain.value_objects.target_system import TargetSystem
from fluxdrive.domain.value_objects.write_mode import WriteMode
from fluxdrive.ui.dialogs.about_dialog import AboutDialog
from fluxdrive.ui.dialogs.download_dialog import DownloadDialog
from fluxdrive.ui.dialogs.drive_properties_dialog import DrivePropertiesDialog
from fluxdrive.ui.dialogs.hash_dialog import HashDialog
from fluxdrive.ui.view_models.main_view_model import MainViewModel

_WINDOW_TITLE = "FluxDrive — Bootable USB Creator"
_WINDOW_MIN_WIDTH = 580
_WINDOW_MIN_HEIGHT = 720


@dataclass
class _DeviceWidgets:
    """Holds widget references for the device selection group."""

    device_combo: QComboBox


@dataclass
class _IsoWidgets:
    """Holds widget references for the ISO selection group."""

    iso_label: QLineEdit
    iso_info_label: QLabel


@dataclass
class _OptionsWidgets:
    """Holds widget references for the write options group."""

    partition_combo: QComboBox
    target_combo: QComboBox
    fs_combo: QComboBox
    cluster_combo: QComboBox
    label_edit: QLineEdit
    mode_combo: QComboBox
    bad_blocks_spin: QSpinBox
    persistent_spin: QSpinBox


@dataclass
class _ProgressWidgets:
    """Holds widget references for the progress display group."""

    progress_bar: QProgressBar
    progress_label: QLabel


@dataclass
class _ActionWidgets:
    """Holds widget references for the action buttons."""

    start_btn: QPushButton
    cancel_btn: QPushButton


class MainWindow(QMainWindow):
    """FluxDrive's main application window.

    Presents device selection, ISO selection, write options, progress,
    and a log panel. Delegates all logic to MainViewModel following MVVM.
    """

    def __init__(self, view_model: MainViewModel) -> None:
        """Initialize the main window and connect all signals.

        Args:
            view_model: The MainViewModel instance (Dependency Injection).
        """
        super().__init__()
        self._vm = view_model
        self._selected_iso_path: Path | None = None
        self._devices: list[Device] = []
        self._log_view: QTextEdit
        self._status_bar: QStatusBar
        self._device_widgets: _DeviceWidgets
        self._iso_widgets: _IsoWidgets
        self._options_widgets: _OptionsWidgets
        self._progress_widgets: _ProgressWidgets
        self._action_widgets: _ActionWidgets

        self._setup_window()
        self._build_ui()
        self._connect_signals()
        self._vm.refresh_devices()

    def _setup_window(self) -> None:
        """Configure window title, size, and icon."""
        self.setWindowTitle(_WINDOW_TITLE)
        self.setMinimumSize(_WINDOW_MIN_WIDTH, _WINDOW_MIN_HEIGHT)
        self.setWindowIcon(QIcon.fromTheme("drive-removable-media"))

    def _build_ui(self) -> None:
        """Construct and arrange all UI widgets."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        layout.addWidget(self._build_device_group())
        layout.addWidget(self._build_iso_group())
        layout.addWidget(self._build_options_group())
        layout.addWidget(self._build_progress_group())
        layout.addWidget(self._build_log_group())
        layout.addLayout(self._build_action_buttons())

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready.")

        self._build_menu_bar()

    def _build_device_group(self) -> QGroupBox:
        """Build the device selection group box.

        Returns:
            Configured QGroupBox for device selection.
        """
        group = QGroupBox("Device")
        layout = QHBoxLayout(group)

        device_combo = QComboBox()
        device_combo.setMinimumWidth(300)
        device_combo.setToolTip("Select the target USB drive.")
        self._device_widgets = _DeviceWidgets(device_combo=device_combo)

        refresh_btn = QPushButton("↺")
        refresh_btn.setFixedWidth(32)
        refresh_btn.setToolTip("Refresh device list")
        refresh_btn.clicked.connect(self._on_refresh_devices)

        props_btn = QPushButton("Properties")
        props_btn.setToolTip("Show device details")
        props_btn.clicked.connect(self._on_show_device_properties)

        layout.addWidget(device_combo, stretch=1)
        layout.addWidget(refresh_btn)
        layout.addWidget(props_btn)
        return group

    def _build_iso_group(self) -> QGroupBox:
        """Build the ISO file selection group box.

        Returns:
            Configured QGroupBox for ISO selection.
        """
        group = QGroupBox("Boot Selection")
        layout = QVBoxLayout(group)

        row1 = QHBoxLayout()
        iso_label = QLineEdit()
        iso_label.setPlaceholderText("No ISO selected — format only")
        iso_label.setReadOnly(True)

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._on_browse_iso)

        hash_btn = QPushButton("Check Hash")
        hash_btn.setToolTip("Verify ISO integrity with MD5/SHA1/SHA256/SHA512")
        hash_btn.clicked.connect(self._on_check_hash)

        download_btn = QPushButton("Download ISO")
        download_btn.setToolTip("Download a Linux distribution ISO")
        download_btn.clicked.connect(self._on_open_downloader)

        row1.addWidget(iso_label, stretch=1)
        row1.addWidget(browse_btn)
        row1.addWidget(hash_btn)
        row1.addWidget(download_btn)

        iso_info_label = QLabel("")
        iso_info_label.setStyleSheet("color: #888; font-size: 11px;")
        self._iso_widgets = _IsoWidgets(iso_label=iso_label, iso_info_label=iso_info_label)

        layout.addLayout(row1)
        layout.addWidget(iso_info_label)
        return group

    def _build_options_row1(self) -> QHBoxLayout:
        """Build the partition scheme and target system option row.

        Returns:
            QHBoxLayout with partition scheme and target system combos.
        """
        row = QHBoxLayout()
        row.addWidget(QLabel("Partition Scheme:"))
        partition_combo = QComboBox()
        for scheme in PartitionScheme:
            partition_combo.addItem(scheme.label(), scheme)
        row.addWidget(partition_combo)

        row.addWidget(QLabel("Target System:"))
        target_combo = QComboBox()
        for target in TargetSystem:
            target_combo.addItem(target.label(), target)
        row.addWidget(target_combo)

        self._options_widgets.partition_combo = partition_combo
        self._options_widgets.target_combo = target_combo
        return row

    def _build_options_row2(self) -> QHBoxLayout:
        """Build the file system and cluster size option row.

        Returns:
            QHBoxLayout with filesystem and cluster size combos.
        """
        row = QHBoxLayout()
        row.addWidget(QLabel("File System:"))
        fs_combo = QComboBox()
        for fs in FileSystem:
            fs_combo.addItem(fs.label(), fs)
        row.addWidget(fs_combo)

        row.addWidget(QLabel("Cluster Size:"))
        cluster_combo = QComboBox()
        for cs in ClusterSize:
            cluster_combo.addItem(cs.label(), cs)
        row.addWidget(cluster_combo)

        self._options_widgets.fs_combo = fs_combo
        self._options_widgets.cluster_combo = cluster_combo
        return row

    def _build_options_row3(self) -> QHBoxLayout:
        """Build the volume label and write mode option row.

        Returns:
            QHBoxLayout with label edit and write mode combo.
        """
        row = QHBoxLayout()
        row.addWidget(QLabel("Volume Label:"))
        label_edit = QLineEdit()
        label_edit.setMaxLength(11)
        label_edit.setPlaceholderText("FLUXDRIVE")
        row.addWidget(label_edit)

        row.addWidget(QLabel("Write Mode:"))
        mode_combo = QComboBox()
        for mode in WriteMode:
            mode_combo.addItem(mode.label(), mode)
        row.addWidget(mode_combo)

        self._options_widgets.label_edit = label_edit
        self._options_widgets.mode_combo = mode_combo
        return row

    def _build_options_row4(self) -> QHBoxLayout:
        """Build the bad blocks passes and persistent partition option row.

        Returns:
            QHBoxLayout with bad blocks and persistent partition spinboxes.
        """
        row = QHBoxLayout()
        row.addWidget(QLabel("Bad Blocks Passes:"))
        bad_blocks_spin = QSpinBox()
        bad_blocks_spin.setRange(0, 4)
        bad_blocks_spin.setValue(0)
        bad_blocks_spin.setSpecialValueText("None")
        row.addWidget(bad_blocks_spin)

        row.addWidget(QLabel("Persistent Partition (MiB):"))
        persistent_spin = QSpinBox()
        persistent_spin.setRange(0, 65536)
        persistent_spin.setValue(0)
        persistent_spin.setSpecialValueText("None")
        row.addWidget(persistent_spin)

        self._options_widgets.bad_blocks_spin = bad_blocks_spin
        self._options_widgets.persistent_spin = persistent_spin
        return row

    def _build_options_group(self) -> QGroupBox:
        """Build the write options group box.

        Returns:
            Configured QGroupBox for all write options.
        """
        group = QGroupBox("Options")
        grid_layout = QVBoxLayout(group)

        self._options_widgets = _OptionsWidgets(
            partition_combo=QComboBox(),
            target_combo=QComboBox(),
            fs_combo=QComboBox(),
            cluster_combo=QComboBox(),
            label_edit=QLineEdit(),
            mode_combo=QComboBox(),
            bad_blocks_spin=QSpinBox(),
            persistent_spin=QSpinBox(),
        )

        grid_layout.addLayout(self._build_options_row1())
        grid_layout.addLayout(self._build_options_row2())
        grid_layout.addLayout(self._build_options_row3())
        grid_layout.addLayout(self._build_options_row4())
        return group

    def _build_progress_group(self) -> QGroupBox:
        """Build the progress display group box.

        Returns:
            Configured QGroupBox with progress bar and status label.
        """
        group = QGroupBox("Progress")
        layout = QVBoxLayout(group)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)

        progress_label = QLabel("Ready.")
        progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress_widgets = _ProgressWidgets(
            progress_bar=progress_bar,
            progress_label=progress_label,
        )

        layout.addWidget(progress_bar)
        layout.addWidget(progress_label)
        return group

    def _build_log_group(self) -> QGroupBox:
        """Build the operation log group box.

        Returns:
            Configured QGroupBox with read-only log text area.
        """
        group = QGroupBox("Log")
        layout = QVBoxLayout(group)

        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumHeight(120)
        self._log_view.setFontFamily("monospace")

        layout.addWidget(self._log_view)
        return group

    def _build_action_buttons(self) -> QHBoxLayout:
        """Build the bottom action button row.

        Returns:
            QHBoxLayout containing Start and Cancel buttons.
        """
        layout = QHBoxLayout()

        start_btn = QPushButton("START")
        start_btn.setMinimumHeight(40)
        start_btn.setStyleSheet(
            "QPushButton { background-color: #2a7af5; color: white; "
            "font-weight: bold; border-radius: 4px; } "
            "QPushButton:hover { background-color: #1a6ae5; } "
            "QPushButton:disabled { background-color: #888; }"
        )
        start_btn.clicked.connect(self._on_start)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setEnabled(False)
        cancel_btn.clicked.connect(self._on_cancel)

        self._action_widgets = _ActionWidgets(start_btn=start_btn, cancel_btn=cancel_btn)

        layout.addWidget(start_btn)
        layout.addWidget(cancel_btn)
        return layout

    def _build_menu_bar(self) -> None:
        """Construct the application menu bar."""
        menubar = self.menuBar()
        assert menubar is not None

        file_menu = menubar.addMenu("File")
        assert file_menu is not None
        file_menu.addAction("Open ISO…", self._on_browse_iso)
        file_menu.addSeparator()
        file_menu.addAction("Exit", QApplication.quit)

        tools_menu = menubar.addMenu("Tools")
        assert tools_menu is not None
        tools_menu.addAction("Download ISO…", self._on_open_downloader)
        tools_menu.addAction("Check Hash…", self._on_check_hash)
        tools_menu.addAction("Device Properties…", self._on_show_device_properties)

        help_menu = menubar.addMenu("Help")
        assert help_menu is not None
        help_menu.addAction("About FluxDrive", self._on_about)

    def _connect_signals(self) -> None:
        """Wire view model signals to UI update slots."""
        self._vm.devices_refreshed.connect(self._on_devices_refreshed)
        self._vm.iso_detected.connect(self._on_iso_detected)
        self._vm.write_progress.connect(self._on_write_progress)
        self._vm.write_finished.connect(self._on_write_finished)
        self._vm.write_error.connect(self._on_write_error)
        self._vm.log_message.connect(self._append_log)
        self._vm.hash_computed.connect(self._on_hash_computed)

    def _on_refresh_devices(self) -> None:
        """Handle device refresh button click."""
        self._vm.refresh_devices()

    def _on_devices_refreshed(self, devices: list[Device]) -> None:
        """Populate the device combo box with the refreshed list.

        Args:
            devices: List of Device entities.
        """
        self._devices = devices
        self._device_widgets.device_combo.clear()
        for device in devices:
            self._device_widgets.device_combo.addItem(device.display_name(), device)
        if not devices:
            self._device_widgets.device_combo.addItem("No removable devices found", None)

    def _on_browse_iso(self) -> None:
        """Open a file dialog to select an ISO or IMG file."""
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open ISO Image",
            str(Path.home()),
            "Disk Images (*.iso *.img *.ISO *.IMG);;All Files (*)",
        )
        if path_str:
            iso_path = Path(path_str)
            self._selected_iso_path = iso_path
            self._iso_widgets.iso_label.setText(str(iso_path))
            self._vm.detect_iso(iso_path)

    def _on_iso_detected(self, iso: object) -> None:
        """Update the ISO info label with detected boot capabilities.

        Args:
            iso: IsoImage entity with detected properties.
        """
        if isinstance(iso, IsoImage):
            bios = "BIOS" if iso.has_bios else ""
            uefi = "UEFI" if iso.has_uefi else ""
            boot_str = " + ".join(filter(None, [bios, uefi])) or "Unknown"
            self._iso_widgets.iso_info_label.setText(
                f"  {iso.size_label()}  |  Boot: {boot_str}"
                f"{'  |  Hybrid' if iso.is_hybrid else ''}"
                f"{'  |  Label: ' + iso.label if iso.label else ''}"
            )

    def _on_check_hash(self) -> None:
        """Open the hash verification dialog."""
        if self._selected_iso_path is None:
            QMessageBox.information(self, "No ISO", "Please select an ISO file first.")
            return
        dialog = HashDialog(self._selected_iso_path, self._vm, self)
        dialog.exec()

    def _on_open_downloader(self) -> None:
        """Open the ISO download dialog."""
        dialog = DownloadDialog(self._vm, self)
        dialog.exec()

    def _on_show_device_properties(self) -> None:
        """Open the device properties dialog for the selected device."""
        current_data = self._device_widgets.device_combo.currentData()
        if current_data is None:
            QMessageBox.information(self, "No Device", "Please select a device first.")
            return
        dialog = DrivePropertiesDialog(current_data, self)
        dialog.exec()

    def _on_start(self) -> None:
        """Validate the configuration and start the write operation."""
        device_data = self._device_widgets.device_combo.currentData()
        if device_data is None:
            QMessageBox.warning(self, "No Device", "Please select a target device.")
            return

        if not self._confirm_overwrite(device_data):
            return

        config = self._build_write_config(device_data)
        self._set_ui_writing_state(True)
        self._vm.start_write(config)

    def _confirm_overwrite(self, device: object) -> bool:
        """Show a confirmation dialog before writing.

        Args:
            device: Device entity to display in the confirmation message.

        Returns:
            True if the user confirmed the operation.
        """
        device_str = device.display_name() if isinstance(device, Device) else str(device)
        reply = QMessageBox.warning(
            self,
            "Confirm Write",
            f"WARNING: All data on {device_str} will be permanently destroyed.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _build_write_config(self, device: object) -> WriteConfig:
        """Construct a WriteConfig from the current UI state.

        Args:
            device: The selected Device entity.

        Returns:
            Populated WriteConfig instance.
        """
        assert isinstance(device, Device)

        iso: IsoImage | None = None
        if self._selected_iso_path is not None:
            iso = IsoImage(
                path=self._selected_iso_path,
                size_bytes=self._selected_iso_path.stat().st_size,
            )

        opts = self._options_widgets
        return WriteConfig(
            device=device,
            iso_image=iso,
            partition_scheme=opts.partition_combo.currentData(),
            target_system=opts.target_combo.currentData(),
            file_system=opts.fs_combo.currentData(),
            cluster_size=opts.cluster_combo.currentData(),
            volume_label=opts.label_edit.text().strip(),
            write_mode=opts.mode_combo.currentData(),
            check_bad_blocks=opts.bad_blocks_spin.value(),
            create_persistent=opts.persistent_spin.value(),
        )

    def _on_write_progress(self, percent: int, message: str) -> None:
        """Update progress bar and status label.

        Args:
            percent: Progress value (0–100).
            message: Status message.
        """
        self._progress_widgets.progress_bar.setValue(percent)
        if message:
            self._progress_widgets.progress_label.setText(message)

    def _on_write_finished(self) -> None:
        """Handle successful write completion."""
        self._set_ui_writing_state(False)
        self._progress_widgets.progress_bar.setValue(100)
        self._progress_widgets.progress_label.setText("Done!")
        self._status_bar.showMessage("Write completed successfully.")
        QMessageBox.information(
            self,
            "Success",
            "The USB drive has been created successfully.",
        )

    def _on_write_error(self, message: str) -> None:
        """Handle write error by resetting UI and showing error dialog.

        Args:
            message: Error description.
        """
        self._set_ui_writing_state(False)
        self._progress_widgets.progress_label.setText("Error.")
        self._status_bar.showMessage(f"Error: {message}")
        QMessageBox.critical(self, "Write Error", message)

    def _on_cancel(self) -> None:
        """Cancel the in-progress write operation."""
        QMessageBox.information(
            self,
            "Cancel",
            "Cancellation is not yet implemented. "
            "Wait for the current operation to complete or force-close the application.",
        )

    def _on_hash_computed(self, digest: str) -> None:
        """Display the computed hash in the status bar.

        Args:
            digest: Hex digest string.
        """
        self._status_bar.showMessage(f"Hash: {digest}")

    def _on_about(self) -> None:
        """Open the About dialog."""
        AboutDialog(self).exec()

    def _append_log(self, message: str) -> None:
        """Append a message to the log view and scroll to bottom.

        Args:
            message: Log entry to append.
        """
        self._log_view.append(message)
        scrollbar = self._log_view.verticalScrollBar()
        assert scrollbar is not None
        scrollbar.setValue(scrollbar.maximum())

    def _set_ui_writing_state(self, writing: bool) -> None:
        """Enable or disable UI controls based on write state.

        Args:
            writing: True when a write operation is in progress.
        """
        self._action_widgets.start_btn.setEnabled(not writing)
        self._action_widgets.cancel_btn.setEnabled(writing)
        self._device_widgets.device_combo.setEnabled(not writing)
