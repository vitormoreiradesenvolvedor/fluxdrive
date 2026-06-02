"""udev-based device scanner — concrete IDeviceScanner for Linux."""

from pathlib import Path

import pyudev

from fluxdrive.application.contracts.i_device_scanner import IDeviceScanner
from fluxdrive.domain.entities.device import Device
from fluxdrive.domain.exceptions.device_errors import DeviceNotFoundError


class UdevDeviceScanner(IDeviceScanner):
    """Lists removable block devices using the Linux udev subsystem.

    Uses pyudev to enumerate block devices and reads sysfs attributes
    to determine removability, size, and partition layout.
    """

    _BLOCK_SUBSYSTEM = "block"
    _DISK_DEVTYPE = "disk"
    _REMOVABLE_SYSATTR = "removable"

    def __init__(self) -> None:
        """Initialize the udev context."""
        self._context = pyudev.Context()

    def list_removable_devices(self) -> list[Device]:
        """Return all removable block devices currently connected.

        Returns:
            List of Device entities for all removable drives found.
        """
        devices: list[Device] = []

        for udev_device in self._context.list_devices(
            subsystem=self._BLOCK_SUBSYSTEM, DEVTYPE=self._DISK_DEVTYPE
        ):
            if self._is_removable(udev_device):
                device = self._build_device(udev_device)
                if device is not None:
                    devices.append(device)

        return sorted(devices, key=lambda d: str(d.path))

    def get_device(self, path: str) -> Device:
        """Return a Device entity for the given block device path.

        Args:
            path: Absolute block device path (e.g. '/dev/sdb').

        Raises:
            DeviceNotFoundError: If the path does not match any device.
        """
        udev_device = pyudev.Device.from_device_file(self._context, path)
        if udev_device is None:
            raise DeviceNotFoundError(f"Device not found: {path}")
        device = self._build_device(udev_device)
        if device is None:
            raise DeviceNotFoundError(f"Could not read device attributes for: {path}")
        return device

    def _is_removable(self, udev_device: pyudev.Device) -> bool:
        """Return True if the udev device is marked as removable.

        Args:
            udev_device: The udev Device object to check.
        """
        removable = udev_device.attributes.asstring(self._REMOVABLE_SYSATTR)
        return bool(removable.strip() == "1")

    def _build_device(self, udev_device: pyudev.Device) -> Device | None:
        """Construct a Device entity from a udev Device object.

        Args:
            udev_device: The udev Device object to convert.

        Returns:
            A Device entity, or None if required attributes are missing.
        """
        try:
            path = Path(udev_device.device_node)
            size_bytes = self._read_size(udev_device)
            name = (
                udev_device.get("ID_MODEL", "") or udev_device.get("ID_FS_LABEL", "") or path.name
            )
            vendor = udev_device.get("ID_VENDOR", "")
            model = udev_device.get("ID_MODEL", "")
            partitions = self._list_partitions(udev_device)

            return Device(
                path=path,
                name=name,
                size_bytes=size_bytes,
                is_removable=True,
                vendor=vendor,
                model=model,
                partitions=tuple(partitions),
            )
        except (ValueError, KeyError):
            return None

    def _read_size(self, udev_device: pyudev.Device) -> int:
        """Read the device size in bytes from the sysfs 'size' attribute.

        Args:
            udev_device: The udev Device object.

        Returns:
            Device size in bytes (sectors × 512).
        """
        size_attr = udev_device.attributes.asstring("size")
        sectors = int(size_attr.strip())
        return sectors * 512

    def _list_partitions(self, udev_device: pyudev.Device) -> list[str]:
        """Return the device paths of all partitions on this disk.

        Args:
            udev_device: The parent disk's udev Device object.
        """
        partitions: list[str] = []
        for child in udev_device.children:
            if child.device_type == "partition" and child.device_node:
                partitions.append(child.device_node)
        return sorted(partitions)
