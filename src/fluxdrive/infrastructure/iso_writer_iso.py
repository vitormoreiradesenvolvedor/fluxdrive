"""ISO-mode writer — extracts ISO contents and installs bootloader."""

import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from fluxdrive.application.contracts.i_iso_writer import IIsoWriter
from fluxdrive.domain.entities.write_config import WriteConfig
from fluxdrive.domain.exceptions.write_errors import BootloaderInstallError, WriteError
from fluxdrive.domain.value_objects.target_system import TargetSystem
from fluxdrive.domain.value_objects.write_mode import WriteMode
from fluxdrive.infrastructure.drive_formatter import DriveFormatter


class IsoModeWriter(IIsoWriter):
    """Writes a bootable USB in ISO mode: formats, copies files, installs bootloader.

    Supports BIOS (via syslinux/GRUB), UEFI (via grub-efi), and dual boot.
    This mode allows adding extra files and a persistent partition after writing.
    """

    def __init__(self) -> None:
        """Initialize with a DriveFormatter dependency."""
        self._formatter = DriveFormatter()

    def can_handle(self, config: WriteConfig) -> bool:
        """Return True when the config specifies ISO image write mode.

        Args:
            config: The write configuration to evaluate.
        """
        return config.write_mode == WriteMode.ISO_IMAGE

    def write(
        self,
        config: WriteConfig,
        progress_callback: Callable[[int, str], None],
    ) -> None:
        """Format, copy files, and install bootloader on the target device.

        Args:
            config: Write configuration with iso_image set.
            progress_callback: Called with (percent: int, message: str).

        Raises:
            WriteError: If any step of the write process fails.
        """
        if config.iso_image is None:
            raise WriteError("ISO mode writer requires an ISO image.")

        progress_callback(0, "Formatting device…")
        self._formatter.format(config, lambda p, m: progress_callback(p // 4, m))

        progress_callback(25, "Mounting ISO…")
        with tempfile.TemporaryDirectory(prefix="fluxdrive-iso-") as mount_dir:
            self._mount_iso(config.iso_image.path, Path(mount_dir))

            progress_callback(30, "Copying files from ISO…")
            partition = self._get_partition_path(str(config.device.path))
            with tempfile.TemporaryDirectory(prefix="fluxdrive-dev-") as dev_dir:
                self._mount_device(partition, Path(dev_dir))
                self._copy_files(Path(mount_dir), Path(dev_dir), progress_callback)
                progress_callback(85, "Installing bootloader…")
                self._install_bootloader(config, Path(dev_dir), Path(mount_dir))
                self._unmount(Path(dev_dir))

            self._unmount(Path(mount_dir))

        if config.create_persistent > 0:
            progress_callback(92, "Creating persistent partition…")
            self._add_persistent_partition(
                str(config.device.path), config.create_persistent
            )

        progress_callback(98, "Flushing buffers…")
        subprocess.run(["sync"], check=True)
        progress_callback(100, "Write complete.")

    def _mount_iso(self, iso_path: Path, mount_point: Path) -> None:
        """Loop-mount the ISO file at a temporary directory.

        Args:
            iso_path: Path to the ISO file.
            mount_point: Directory to mount onto.

        Raises:
            WriteError: If mount fails.
        """
        result = subprocess.run(
            ["mount", "-o", "loop,ro", str(iso_path), str(mount_point)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise WriteError(f"Failed to mount ISO: {result.stderr.strip()}")

    def _mount_device(self, partition: str, mount_point: Path) -> None:
        """Mount the formatted partition at the given directory.

        Args:
            partition: Partition device path string.
            mount_point: Directory to mount onto.

        Raises:
            WriteError: If mount fails.
        """
        result = subprocess.run(
            ["mount", partition, str(mount_point)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise WriteError(f"Failed to mount partition: {result.stderr.strip()}")

    def _copy_files(
        self,
        source: Path,
        destination: Path,
        progress_callback: Callable[[int, str], None],
    ) -> None:
        """Copy all files from ISO mount to device mount using rsync.

        Args:
            source: ISO mount directory.
            destination: Device mount directory.
            progress_callback: Progress reporting callback.

        Raises:
            WriteError: If rsync fails.
        """
        result = subprocess.run(
            [
                "rsync",
                "-a",
                "--info=progress2",
                str(source) + "/",
                str(destination) + "/",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode not in (0, 24):
            raise WriteError(f"rsync failed: {result.stderr.strip()}")
        progress_callback(80, "Files copied.")

    def _install_bootloader(
        self,
        config: WriteConfig,
        dev_mount: Path,
        iso_mount: Path,
    ) -> None:
        """Install the appropriate bootloader(s) based on target system.

        Args:
            config: Write configuration with target system info.
            dev_mount: Device mount directory.
            iso_mount: ISO mount directory (source for bootloader files).

        Raises:
            BootloaderInstallError: If bootloader installation fails.
        """
        if config.target_system.requires_bios_bootloader():
            self._install_syslinux(str(config.device.path), dev_mount, iso_mount)
        if config.target_system.requires_uefi_bootloader():
            self._ensure_efi_present(dev_mount, iso_mount)

    def _install_syslinux(
        self, device_path: str, dev_mount: Path, iso_mount: Path
    ) -> None:
        """Install syslinux/isolinux as the BIOS bootloader.

        Args:
            device_path: Block device path.
            dev_mount: Device mount directory.
            iso_mount: ISO mount directory.

        Raises:
            BootloaderInstallError: If syslinux is unavailable or fails.
        """
        syslinux_src = iso_mount / "isolinux"
        if not syslinux_src.exists():
            syslinux_src = iso_mount / "syslinux"

        if syslinux_src.exists():
            syslinux_dst = dev_mount / "syslinux"
            syslinux_dst.mkdir(exist_ok=True)
            subprocess.run(
                ["cp", "-r", str(syslinux_src) + "/.", str(syslinux_dst)],
                check=True,
            )

        result = subprocess.run(
            ["syslinux", "--install", "--directory", "syslinux", f"{device_path}1"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise BootloaderInstallError(
                f"syslinux install failed: {result.stderr.strip()}"
            )

    def _ensure_efi_present(self, dev_mount: Path, iso_mount: Path) -> None:
        """Verify the EFI directory was copied from the ISO.

        Most modern Linux ISOs already include a /EFI directory.
        If present in the ISO, rsync will have already copied it.

        Args:
            dev_mount: Device mount directory.
            iso_mount: ISO mount directory.

        Raises:
            BootloaderInstallError: If no EFI content can be found.
        """
        efi_on_device = dev_mount / "EFI"
        efi_on_iso = iso_mount / "EFI"

        if not efi_on_device.exists():
            if not efi_on_iso.exists():
                raise BootloaderInstallError(
                    "No EFI directory found in the ISO. "
                    "This ISO may not support UEFI boot."
                )

    def _add_persistent_partition(
        self, device_path: str, size_mib: int
    ) -> None:
        """Append a casper-rw persistent partition at the end of the device.

        Args:
            device_path: Block device path.
            size_mib: Desired partition size in MiB.
        """
        result = subprocess.run(
            [
                "parted",
                "-s",
                device_path,
                "mkpart",
                "primary",
                "ext4",
                "-1",
                f"-{max(1, size_mib - 1)}MiB",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            part2 = f"{device_path}2" if not device_path[-1].isdigit() else f"{device_path}p2"
            subprocess.run(
                ["mkfs.ext4", "-L", "casper-rw", part2],
                capture_output=True,
            )

    def _unmount(self, mount_point: Path) -> None:
        """Unmount the given mount point, ignoring errors.

        Args:
            mount_point: The directory to unmount.
        """
        subprocess.run(["umount", str(mount_point)], capture_output=True)

    def _get_partition_path(self, device_path: str) -> str:
        """Derive the first partition path from a disk device path.

        Args:
            device_path: Disk device path string.
        """
        if device_path[-1].isdigit():
            return f"{device_path}p1"
        return f"{device_path}1"
