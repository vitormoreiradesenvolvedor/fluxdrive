"""Write-operation domain exceptions."""


class WriteError(Exception):
    """Base class for all write-operation errors."""


class IsoFileNotFoundError(WriteError):
    """Raised when the specified ISO file does not exist."""


class IsoFileTooLargeError(WriteError):
    """Raised when the ISO file is larger than the target device."""


class BootloaderInstallError(WriteError):
    """Raised when installation of the BIOS or UEFI bootloader fails."""


class PartitioningError(WriteError):
    """Raised when the partitioning step cannot be completed."""


class FormatError(WriteError):
    """Raised when the filesystem creation step fails."""


class BadBlocksError(WriteError):
    """Raised when bad blocks are detected during verification passes."""


class DownloadError(WriteError):
    """Raised when an ISO download fails or is interrupted."""


class HashMismatchError(WriteError):
    """Raised when the computed hash does not match the expected digest."""

    def __init__(self, expected: str, actual: str) -> None:
        """Initialize with both digest values for a descriptive message.

        Args:
            expected: The hash value that was expected.
            actual: The hash value that was computed.
        """
        super().__init__(
            f"Hash mismatch — expected: {expected!r}, got: {actual!r}"
        )
