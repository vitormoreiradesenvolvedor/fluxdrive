"""Hash verification dialog — allows computing and verifying ISO digests."""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fluxdrive.domain.value_objects.hash_algorithm import HashAlgorithm
from fluxdrive.ui.view_models.main_view_model import MainViewModel


class HashDialog(QDialog):
    """Modal dialog for computing and verifying ISO cryptographic hashes.

    The user selects the algorithm, clicks Compute, and optionally
    pastes an expected digest to verify the file's integrity.
    """

    def __init__(self, iso_path: Path, view_model: object, parent: QWidget | None = None) -> None:
        """Initialize the hash dialog for a specific ISO file.

        Args:
            iso_path: Path to the ISO file to verify.
            view_model: MainViewModel instance providing hash operations.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._iso_path = iso_path
        self._vm = view_model

        self.setWindowTitle("Check Hash")
        self.setMinimumWidth(500)
        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the dialog layout."""
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._file_label = QLabel(self._iso_path.name)
        form.addRow("File:", self._file_label)

        self._algo_combo = QComboBox()
        for algo in HashAlgorithm:
            self._algo_combo.addItem(algo.label(), algo)
        form.addRow("Algorithm:", self._algo_combo)

        self._result_edit = QLineEdit()
        self._result_edit.setReadOnly(True)
        self._result_edit.setPlaceholderText("Computed hash will appear here…")
        self._result_edit.setFont(self._result_edit.font())
        form.addRow("Computed:", self._result_edit)

        self._expected_edit = QLineEdit()
        self._expected_edit.setPlaceholderText("Paste expected hash here to verify…")
        form.addRow("Expected:", self._expected_edit)

        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addRow("Status:", self._status_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)

        compute_btn = QPushButton("Compute Hash")
        compute_btn.clicked.connect(self._on_compute)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(self._progress)
        layout.addWidget(compute_btn)
        layout.addWidget(buttons)

    def _on_compute(self) -> None:
        """Compute the hash and optionally verify against the expected value."""
        algo = self._algo_combo.currentData()
        self._status_label.setText("Computing…")
        self._result_edit.clear()

        if isinstance(self._vm, MainViewModel):
            self._vm.compute_hash(self._iso_path, algo)
            self._vm.hash_computed.connect(self._on_hash_ready)
            self._vm.hash_error.connect(self._on_hash_error)

    def _on_hash_ready(self, digest: str) -> None:
        """Display the computed hash and check against expected.

        Args:
            digest: Computed hex digest string.
        """
        self._result_edit.setText(digest)
        expected = self._expected_edit.text().strip().lower()
        if expected:
            if digest.lower() == expected:
                self._status_label.setText("✓ Match — file integrity verified.")
                self._status_label.setStyleSheet("color: green;")
            else:
                self._status_label.setText("✗ Mismatch — file may be corrupt!")
                self._status_label.setStyleSheet("color: red;")
        else:
            self._status_label.setText("Hash computed.")
            self._status_label.setStyleSheet("")

    def _on_hash_error(self, message: str) -> None:
        """Display a hash computation error.

        Args:
            message: Error description.
        """
        self._status_label.setText(f"Error: {message}")
        self._status_label.setStyleSheet("color: red;")
