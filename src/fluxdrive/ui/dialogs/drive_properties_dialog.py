"""Drive properties dialog — shows detailed information about a device."""

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)


class DrivePropertiesDialog(QDialog):
    """Modal dialog displaying detailed properties of a selected device.

    Shows path, model, vendor, size, removability, and partition layout.
    """

    def __init__(self, device: object, parent: object = None) -> None:
        """Initialize the dialog with a Device entity.

        Args:
            device: Device entity to display properties for.
            parent: Optional parent widget.
        """
        super().__init__(parent)  # type: ignore[call-arg]
        self._device = device
        self.setWindowTitle("Device Properties")
        self.setMinimumWidth(400)
        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the properties layout from the device entity."""
        layout = QVBoxLayout(self)
        form = QFormLayout()

        from fluxdrive.domain.entities.device import Device

        if isinstance(self._device, Device):
            dev = self._device
            form.addRow("Path:", QLabel(str(dev.path)))
            form.addRow("Name:", QLabel(dev.name or "Unknown"))
            form.addRow("Vendor:", QLabel(dev.vendor or "Unknown"))
            form.addRow("Model:", QLabel(dev.model or "Unknown"))
            form.addRow("Size:", QLabel(dev.size_label()))
            form.addRow("Removable:", QLabel("Yes" if dev.is_removable else "No"))
            partitions_str = ", ".join(dev.partitions) if dev.partitions else "None detected"
            form.addRow("Partitions:", QLabel(partitions_str))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout.addLayout(form)
        layout.addWidget(buttons)
