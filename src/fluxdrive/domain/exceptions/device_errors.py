"""Device-related domain exceptions."""


class DeviceError(Exception):
    """Base class for all device-related errors."""


class DeviceNotFoundError(DeviceError):
    """Raised when the requested device path does not exist in the system."""


class DeviceNotRemovableError(DeviceError):
    """Raised when attempting to write to a non-removable device."""


class DeviceTooSmallError(DeviceError):
    """Raised when the device capacity is insufficient for the ISO image."""

    def __init__(self, device_bytes: int, required_bytes: int) -> None:
        """Initialize with actual and required sizes for a descriptive message.

        Args:
            device_bytes: Available device capacity in bytes.
            required_bytes: Minimum required capacity in bytes.
        """
        gib_dev = device_bytes / 1024**3
        gib_req = required_bytes / 1024**3
        super().__init__(f"Device has {gib_dev:.2f} GiB but {gib_req:.2f} GiB is required.")


class DeviceBusyError(DeviceError):
    """Raised when the device is mounted or in use by another process."""


class DevicePermissionError(DeviceError):
    """Raised when the process lacks permissions to access the device."""
