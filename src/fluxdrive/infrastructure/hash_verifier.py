"""Hashlib-based hash verifier — concrete IHashVerifier for all platforms."""

import hashlib
from collections.abc import Callable
from pathlib import Path

from fluxdrive.application.contracts.i_hash_verifier import IHashVerifier
from fluxdrive.domain.value_objects.hash_algorithm import HashAlgorithm

_CHUNK_SIZE = 65536  # 64 KiB per read — balances memory and syscall overhead


class HashlibHashVerifier(IHashVerifier):
    """Computes and verifies file hashes using the standard hashlib module.

    Reads files in chunks to support large ISO files without loading
    them entirely into memory. Progress is reported as percentage done.
    """

    def compute(
        self,
        path: Path,
        algorithm: HashAlgorithm,
        progress_callback: Callable[[int], None] | None = None,
    ) -> str:
        """Compute the hash digest of a file.

        Args:
            path: Path to the file.
            algorithm: Hash algorithm to use.
            progress_callback: Optional callable(percent: int).

        Returns:
            Lowercase hex digest string.
        """
        hasher = hashlib.new(algorithm.value)
        file_size = path.stat().st_size
        bytes_read = 0

        with path.open("rb") as fh:
            while chunk := fh.read(_CHUNK_SIZE):
                hasher.update(chunk)
                bytes_read += len(chunk)
                if progress_callback is not None and file_size > 0:
                    progress_callback(int(bytes_read * 100 / file_size))

        return hasher.hexdigest()

    def verify(
        self,
        path: Path,
        algorithm: HashAlgorithm,
        expected_digest: str,
        progress_callback: Callable[[int], None] | None = None,
    ) -> bool:
        """Verify a file against an expected digest.

        Args:
            path: Path to the file.
            algorithm: Hash algorithm to use.
            expected_digest: Expected lowercase hex digest.
            progress_callback: Optional callable(percent: int).

        Returns:
            True if the digest matches.

        Raises:
            HashMismatchError: If the digests do not match.
        """
        from fluxdrive.domain.exceptions.write_errors import HashMismatchError

        actual = self.compute(path, algorithm, progress_callback)
        if actual.lower() != expected_digest.lower():
            raise HashMismatchError(expected=expected_digest, actual=actual)
        return True
