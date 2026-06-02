"""Use case for ISO hash verification."""

from pathlib import Path

from fluxdrive.application.contracts.i_hash_verifier import IHashVerifier
from fluxdrive.domain.exceptions.write_errors import HashMismatchError
from fluxdrive.domain.value_objects.hash_algorithm import HashAlgorithm


class VerifyHashUseCase:
    """Orchestrates ISO integrity verification using a provided hash verifier.

    Follows the Single Responsibility Principle — this class only
    coordinates the hash verification workflow and delegates all
    I/O to the injected IHashVerifier.
    """

    def __init__(self, verifier: IHashVerifier) -> None:
        """Initialize with a concrete hash verifier implementation.

        Args:
            verifier: An IHashVerifier implementation (Dependency Injection).
        """
        self._verifier = verifier

    def compute_hash(
        self,
        path: Path,
        algorithm: HashAlgorithm,
        on_progress: object | None = None,
    ) -> str:
        """Compute the hash of an ISO file.

        Args:
            path: Path to the ISO file.
            algorithm: Hash algorithm to use.
            on_progress: Optional callable(percent: int) for progress reporting.

        Returns:
            Hex digest string in lowercase.
        """
        from collections.abc import Callable

        callback: Callable[[int], None] | None = None
        if callable(on_progress):
            callback = on_progress  # type: ignore[assignment]

        return self._verifier.compute(path, algorithm, callback)

    def verify_against(
        self,
        path: Path,
        algorithm: HashAlgorithm,
        expected: str,
        on_progress: object | None = None,
    ) -> None:
        """Verify an ISO file against a known-good digest.

        Args:
            path: Path to the ISO file.
            algorithm: Hash algorithm that produced the expected digest.
            expected: Expected hex digest (lowercase).
            on_progress: Optional callable(percent: int) for progress reporting.

        Raises:
            HashMismatchError: If the file's digest does not match expected.
        """
        from collections.abc import Callable

        callback: Callable[[int], None] | None = None
        if callable(on_progress):
            callback = on_progress  # type: ignore[assignment]

        actual = self._verifier.compute(path, algorithm, callback)
        if actual.lower() != expected.lower():
            raise HashMismatchError(expected=expected, actual=actual)
