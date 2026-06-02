"""Interface for ISO write operations — Strategy pattern port."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from fluxdrive.domain.entities.write_config import WriteConfig


class IIsoWriter(ABC):
    """Contract for writing an ISO image to a USB device.

    Multiple strategies implement this interface:
    - ISO image mode: extracts files and installs a bootloader.
    - DD image mode: raw byte-for-byte copy.
    """

    @abstractmethod
    def write(
        self,
        config: WriteConfig,
        progress_callback: Callable[[int, str], None],
    ) -> None:
        """Write the ISO from config to the target device.

        Args:
            config: Complete write configuration including device and ISO.
            progress_callback: Called with (percent: int, status_message: str)
                               during the write operation.

        Raises:
            WriteError: If the write operation fails for any reason.
        """

    @abstractmethod
    def can_handle(self, config: WriteConfig) -> bool:
        """Return True if this writer can handle the given configuration.

        Args:
            config: The write configuration to evaluate.
        """
