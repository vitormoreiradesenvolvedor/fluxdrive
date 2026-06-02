"""Write configuration entity — all parameters for a USB write operation."""

from dataclasses import dataclass

from fluxdrive.domain.entities.device import Device
from fluxdrive.domain.entities.iso_image import IsoImage
from fluxdrive.domain.value_objects.cluster_size import ClusterSize
from fluxdrive.domain.value_objects.file_system import FileSystem
from fluxdrive.domain.value_objects.partition_scheme import PartitionScheme
from fluxdrive.domain.value_objects.target_system import TargetSystem
from fluxdrive.domain.value_objects.write_mode import WriteMode


@dataclass(frozen=True)
class WriteConfig:
    """Complete configuration for a single USB write/format operation.

    Encapsulates all user-selected parameters needed to format and write
    an ISO image to a USB device or to format-only without an image.

    Attributes:
        device: Target block device to write to.
        iso_image: Source ISO file, or None for format-only operations.
        partition_scheme: MBR or GPT partition table type.
        target_system: BIOS, UEFI, or Dual boot target.
        file_system: Filesystem to create on the primary partition.
        cluster_size: Allocation unit size (0 = auto-select).
        volume_label: Custom label for the created filesystem.
        write_mode: ISO extraction mode or byte-for-byte DD mode.
        quick_format: True skips bad-block zeroing during format.
        check_bad_blocks: Number of bad-block verification passes (0 = skip).
        create_persistent: Size in MiB of a persistent data partition (0 = none).
    """

    device: Device
    iso_image: IsoImage | None
    partition_scheme: PartitionScheme
    target_system: TargetSystem
    file_system: FileSystem
    cluster_size: ClusterSize = ClusterSize.DEFAULT
    volume_label: str = ""
    write_mode: WriteMode = WriteMode.ISO_IMAGE
    quick_format: bool = True
    check_bad_blocks: int = 0
    create_persistent: int = 0

    def is_format_only(self) -> bool:
        """Return True when no ISO is provided — format-only operation."""
        return self.iso_image is None

    def requires_root(self) -> bool:
        """Return True — all write operations require root privileges."""
        return True
