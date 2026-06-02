"""ISO boot type detector — reads ISO headers to determine boot capabilities."""

import struct
from pathlib import Path

from fluxdrive.application.contracts.i_iso_detector import IIsoDetector
from fluxdrive.domain.entities.iso_image import IsoImage
from fluxdrive.domain.exceptions.write_errors import IsoFileNotFoundError

# ISO 9660 primary volume descriptor is at sector 16 (offset 0x8000)
_PVD_OFFSET = 0x8000
_PVD_LABEL_OFFSET = 40
_PVD_LABEL_LENGTH = 32
_EFI_SIGNATURE = b"EFI PART"
_BIOS_BOOT_SIGNATURE = b"\x55\xaa"
_BIOS_BOOT_OFFSET = 510
_GPT_HEADER_OFFSET = 512


class IsoDetector(IIsoDetector):
    """Reads ISO/IMG file headers to detect BIOS and UEFI boot capabilities.

    Checks for:
    - MBR boot signature at offset 510 (BIOS bootable)
    - El Torito boot catalog (BIOS + UEFI via ISO9660)
    - GPT header at offset 512 (UEFI hybrid indicator)
    - '/EFI/' directory structure presence (UEFI bootable)
    """

    def detect(self, path: Path) -> IsoImage:
        """Analyse an ISO/IMG file and return a populated IsoImage entity.

        Args:
            path: Absolute path to the ISO or IMG file.

        Returns:
            IsoImage with boot flags and label populated.

        Raises:
            IsoFileNotFoundError: If the file does not exist.
        """
        if not path.exists():
            raise IsoFileNotFoundError(f"ISO not found: {path}")

        size = path.stat().st_size
        has_bios = self._check_bios_boot(path)
        has_uefi = self._check_uefi_boot(path)
        label = self._read_volume_label(path)
        is_hybrid = has_bios and has_uefi

        return IsoImage(
            path=path,
            size_bytes=size,
            is_hybrid=is_hybrid,
            has_uefi=has_uefi,
            has_bios=has_bios,
            label=label,
        )

    def _check_bios_boot(self, path: Path) -> bool:
        """Check for an MBR boot signature at offset 510.

        Args:
            path: ISO file path.
        """
        with path.open("rb") as fh:
            fh.seek(_BIOS_BOOT_OFFSET)
            signature = fh.read(2)
        return signature == _BIOS_BOOT_SIGNATURE

    def _check_uefi_boot(self, path: Path) -> bool:
        """Check for a GPT header or EFI System Partition marker.

        Args:
            path: ISO file path.
        """
        with path.open("rb") as fh:
            fh.seek(_GPT_HEADER_OFFSET)
            signature = fh.read(8)
        if signature == _EFI_SIGNATURE:
            return True
        return self._check_efi_catalog_entry(path)

    def _check_efi_catalog_entry(self, path: Path) -> bool:
        """Scan the El Torito boot catalog for an UEFI entry.

        Reads the ISO9660 boot record descriptor to locate the El Torito
        catalog and checks if a UEFI platform (EFI) boot entry is present.

        Args:
            path: ISO file path.
        """
        try:
            with path.open("rb") as fh:
                fh.seek(_PVD_OFFSET - 2048)  # sector 15 = boot record descriptor
                header = fh.read(2048)
            if len(header) < 5 or header[0]:
                return False
            boot_catalog_lba = struct.unpack_from("<I", header, 71)[0]
            catalog_offset = boot_catalog_lba * 2048
            with path.open("rb") as fh:
                fh.seek(catalog_offset)
                catalog = fh.read(2048)
            # UEFI boot entries use platform ID 0xEF (EFI)
            for offset in range(32, len(catalog) - 4, 32):
                if catalog[offset] in (0x88, 0x00) and catalog[offset + 1] == 0xEF:
                    return True
        except (OSError, struct.error):
            pass
        return False

    def _read_volume_label(self, path: Path) -> str:
        """Read the ISO9660 volume label from the Primary Volume Descriptor.

        Args:
            path: ISO file path.

        Returns:
            Volume label string, stripped of whitespace.
        """
        try:
            with path.open("rb") as fh:
                fh.seek(_PVD_OFFSET + _PVD_LABEL_OFFSET)
                raw = fh.read(_PVD_LABEL_LENGTH)
            return raw.decode("ascii", errors="replace").strip()
        except OSError:
            return ""
