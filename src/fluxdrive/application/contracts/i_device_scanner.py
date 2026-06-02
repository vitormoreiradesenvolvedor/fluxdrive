"""Interface for device scanning — Dependency Inversion port."""

from abc import ABC, abstractmethod

from fluxdrive.domain.entities.device import Device


class IDeviceScanner(ABC):
    """Contract for listing block devices available on the system.

    Implementations may use udev, sysfs, or any OS-specific mechanism.
    The interface exists to decouple use cases from the OS API.
    """

    @abstractmethod
    def list_removable_devices(self) -> list[Device]:
        """Return all removable storage devices currently connected.

        Returns:
            A list of Device entities. May be empty if no devices are found.
        """

    @abstractmethod
    def get_device(self, path: str) -> Device:
        """Return a Device entity for the given block device path.

        Args:
            path: Absolute block device path (e.g. '/dev/sdb').

        Raises:
            DeviceNotFoundError: If the device does not exist.
        """
