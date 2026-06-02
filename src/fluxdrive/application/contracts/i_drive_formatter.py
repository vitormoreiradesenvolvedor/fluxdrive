"""Interface for drive formatting operations."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from fluxdrive.domain.entities.write_config import WriteConfig


class IDriveFormatter(ABC):
    """Contract for partitioning and formatting a USB drive.

    Handles partition table creation and filesystem formatting,
    independently of any ISO writing step.
    """

    @abstractmethod
    def format(
        self,
        config: WriteConfig,
        progress_callback: Callable[[int, str], None],
    ) -> None:
        """Partition and format the target device according to config.

        Args:
            config: Write configuration specifying partition scheme,
                    filesystem, volume label, and cluster size.
            progress_callback: Called with (percent: int, status_message: str).

        Raises:
            PartitioningError: If partition table creation fails.
            FormatError: If filesystem creation fails.
        """
