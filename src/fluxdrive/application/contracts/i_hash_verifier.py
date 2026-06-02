"""Interface for ISO hash verification."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

from fluxdrive.domain.value_objects.hash_algorithm import HashAlgorithm


class IHashVerifier(ABC):
    """Contract for computing and verifying cryptographic hash digests of files."""

    @abstractmethod
    def compute(
        self,
        path: Path,
        algorithm: HashAlgorithm,
        progress_callback: Callable[[int], None] | None = None,
    ) -> str:
        """Compute the hash digest of a file.

        Args:
            path: Path to the file to hash.
            algorithm: Hashing algorithm to use.
            progress_callback: Optional callback with (percent: int).

        Returns:
            Lowercase hex digest string.

        Raises:
            FileNotFoundError: If the file does not exist.
        """

    @abstractmethod
    def verify(
        self,
        path: Path,
        algorithm: HashAlgorithm,
        expected_digest: str,
        progress_callback: Callable[[int], None] | None = None,
    ) -> bool:
        """Verify that a file matches an expected digest.

        Args:
            path: Path to the file to verify.
            algorithm: Hashing algorithm to use.
            expected_digest: Expected lowercase hex digest string.
            progress_callback: Optional callback with (percent: int).

        Returns:
            True if the file matches the expected digest.

        Raises:
            HashMismatchError: If the digests do not match.
        """
