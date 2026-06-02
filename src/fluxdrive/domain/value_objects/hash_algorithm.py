"""Hash algorithm value object — digest algorithm for ISO verification."""

from enum import Enum, unique


@unique
class HashAlgorithm(str, Enum):
    """Supported cryptographic hash algorithms for ISO integrity verification."""

    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"

    def label(self) -> str:
        """Return a human-readable label for display in the UI."""
        return self.value.upper()

    def digest_length(self) -> int:
        """Return the expected hex digest string length."""
        lengths = {
            HashAlgorithm.MD5: 32,
            HashAlgorithm.SHA1: 40,
            HashAlgorithm.SHA256: 64,
            HashAlgorithm.SHA512: 128,
        }
        return lengths[self]
