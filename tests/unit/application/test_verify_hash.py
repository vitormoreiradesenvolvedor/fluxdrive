"""Unit tests for the VerifyHashUseCase."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fluxdrive.application.use_cases.verify_hash_use_case import VerifyHashUseCase
from fluxdrive.domain.exceptions.write_errors import HashMismatchError
from fluxdrive.domain.value_objects.hash_algorithm import HashAlgorithm


@pytest.mark.unit
class TestVerifyHashUseCase:
    """Tests for VerifyHashUseCase delegation and error propagation."""

    def test_compute_hash_delegates_to_verifier(
        self, mock_hash_verifier: MagicMock
    ) -> None:
        """compute_hash() returns the value from the injected verifier."""
        mock_hash_verifier.compute.return_value = "abc123"
        use_case = VerifyHashUseCase(verifier=mock_hash_verifier)

        result = use_case.compute_hash(Path("/tmp/test.iso"), HashAlgorithm.SHA256)

        mock_hash_verifier.compute.assert_called_once()
        assert result == "abc123"

    def test_verify_against_raises_on_mismatch(
        self, mock_hash_verifier: MagicMock
    ) -> None:
        """verify_against() raises HashMismatchError when digests differ."""
        mock_hash_verifier.compute.return_value = "actual_digest"
        use_case = VerifyHashUseCase(verifier=mock_hash_verifier)

        with pytest.raises(HashMismatchError):
            use_case.verify_against(
                Path("/tmp/test.iso"),
                HashAlgorithm.SHA256,
                "expected_different_digest",
            )

    def test_verify_against_succeeds_on_match(
        self, mock_hash_verifier: MagicMock
    ) -> None:
        """verify_against() does not raise when digest matches."""
        mock_hash_verifier.compute.return_value = "correctdigest"
        use_case = VerifyHashUseCase(verifier=mock_hash_verifier)

        use_case.verify_against(
            Path("/tmp/test.iso"),
            HashAlgorithm.SHA256,
            "correctdigest",
        )
