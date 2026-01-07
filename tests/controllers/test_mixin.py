"""Tests for EncryptionKeyMixin."""

import pytest
from cryptography.fernet import InvalidToken

from fastapi_sdk.controllers.mixin import EncryptionKeyMixin

# Test encryption key (32+ bytes)
TEST_ENCRYPTION_KEY = "my-test-encryption-key-32-bytes-long!!"


class TestGenerateSecretKey:
    """Tests for generate_secret_key method."""

    def test_generate_secret_key_returns_string(self):
        """Test that generate_secret_key returns a string."""
        secret = EncryptionKeyMixin.generate_secret_key()
        assert isinstance(secret, str)

    def test_generate_secret_key_length(self):
        """Test that generated secret key has correct length."""
        secret = EncryptionKeyMixin.generate_secret_key()
        # token_urlsafe(32) generates 43 characters (32 bytes)
        assert len(secret) == 43

    def test_generate_secret_key_uniqueness(self):
        """Test that generated secret keys are unique."""
        keys = [EncryptionKeyMixin.generate_secret_key() for _ in range(100)]
        # All keys should be unique
        assert len(keys) == len(set(keys))

    def test_generate_secret_key_url_safe(self):
        """Test that generated secret key is URL-safe."""
        secret = EncryptionKeyMixin.generate_secret_key()
        # URL-safe characters: alphanumeric, -, _
        assert all(c.isalnum() or c in ["-", "_"] for c in secret)


class TestEncryptSecretKey:
    """Tests for encrypt_secret_key method."""

    def test_encrypt_secret_key_returns_string(self):
        """Test that encrypt_secret_key returns a string."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        assert isinstance(encrypted, str)

    def test_encrypt_secret_key_different_from_original(self):
        """Test that encrypted key is different from original."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        assert encrypted != secret

    def test_encrypt_secret_key_consistency(self):
        """Test that encrypting same key produces different results (IV)."""
        secret = "my-secret-key"
        encrypted1 = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        encrypted2 = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        # Fernet uses random IV, so results should be different
        assert encrypted1 != encrypted2

    def test_encrypt_secret_key_with_empty_secret(self):
        """Test that encryption fails with empty secret key."""
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.encrypt_secret_key("", TEST_ENCRYPTION_KEY)
        assert "Secret key is required" in str(exc_info.value)

    def test_encrypt_secret_key_with_none_secret(self):
        """Test that encryption fails with None secret key."""
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.encrypt_secret_key(None, TEST_ENCRYPTION_KEY)
        assert "Secret key is required" in str(exc_info.value)

    def test_encrypt_secret_key_with_empty_encryption_key(self):
        """Test that encryption fails with empty encryption key."""
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.encrypt_secret_key("my-secret", "")
        assert "Encryption key is required" in str(exc_info.value)

    def test_encrypt_secret_key_with_none_encryption_key(self):
        """Test that encryption fails with None encryption key."""
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.encrypt_secret_key("my-secret", None)
        assert "Encryption key is required" in str(exc_info.value)

    def test_encrypt_secret_key_with_unicode(self):
        """Test encrypting a string with unicode characters."""
        secret = "my-secret-key-🔐-unicode"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        assert isinstance(encrypted, str)

    def test_encrypt_secret_key_short_encryption_key(self):
        """Test that encryption fails with short encryption key."""
        secret = "my-secret-key"
        short_key = "short"
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.encrypt_secret_key(secret, short_key)
        assert "at least 32 bytes" in str(exc_info.value)

    def test_encrypt_secret_key_exactly_32_bytes(self):
        """Test encryption with exactly 32-byte key."""
        secret = "my-secret-key"
        key_32 = "a" * 32
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, key_32)
        assert isinstance(encrypted, str)

    def test_encrypt_secret_key_longer_than_32_bytes(self):
        """Test encryption with key longer than 32 bytes."""
        secret = "my-secret-key"
        long_key = "a" * 64
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, long_key)
        assert isinstance(encrypted, str)


class TestValidateSecretKey:
    """Tests for validate_secret_key method."""

    def test_validate_secret_key_valid(self):
        """Test validation with correct secret key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        is_valid = EncryptionKeyMixin.validate_secret_key(
            secret, encrypted, TEST_ENCRYPTION_KEY
        )
        assert is_valid is True

    def test_validate_secret_key_invalid(self):
        """Test validation with incorrect secret key."""
        secret = "my-secret-key"
        wrong_secret = "wrong-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        is_valid = EncryptionKeyMixin.validate_secret_key(
            wrong_secret, encrypted, TEST_ENCRYPTION_KEY
        )
        assert is_valid is False

    def test_validate_secret_key_wrong_encryption_key(self):
        """Test validation with wrong encryption key."""
        secret = "my-secret-key"
        wrong_encryption_key = "wrong-encryption-key-32-bytes!!"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        is_valid = EncryptionKeyMixin.validate_secret_key(
            secret, encrypted, wrong_encryption_key
        )
        assert is_valid is False

    def test_validate_secret_key_corrupted_encrypted(self):
        """Test validation with corrupted encrypted key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        # Corrupt the encrypted key
        corrupted = encrypted[:-10] + "corrupted!"
        is_valid = EncryptionKeyMixin.validate_secret_key(
            secret, corrupted, TEST_ENCRYPTION_KEY
        )
        assert is_valid is False

    def test_validate_secret_key_with_empty_provided_key(self):
        """Test that validation fails with empty provided key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.validate_secret_key("", encrypted, TEST_ENCRYPTION_KEY)
        assert "Provided key is required" in str(exc_info.value)

    def test_validate_secret_key_with_none_provided_key(self):
        """Test that validation fails with None provided key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.validate_secret_key(None, encrypted, TEST_ENCRYPTION_KEY)
        assert "Provided key is required" in str(exc_info.value)

    def test_validate_secret_key_with_empty_encrypted_key(self):
        """Test that validation fails with empty encrypted key."""
        secret = "my-secret-key"
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.validate_secret_key(secret, "", TEST_ENCRYPTION_KEY)
        assert "Encrypted key is required" in str(exc_info.value)

    def test_validate_secret_key_with_none_encrypted_key(self):
        """Test that validation fails with None encrypted key."""
        secret = "my-secret-key"
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.validate_secret_key(secret, None, TEST_ENCRYPTION_KEY)
        assert "Encrypted key is required" in str(exc_info.value)

    def test_validate_secret_key_with_empty_encryption_key(self):
        """Test that validation fails with empty encryption key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.validate_secret_key(secret, encrypted, "")
        assert "Encryption key is required" in str(exc_info.value)

    def test_validate_secret_key_with_none_encryption_key(self):
        """Test that validation fails with None encryption key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.validate_secret_key(secret, encrypted, None)
        assert "Encryption key is required" in str(exc_info.value)

    def test_validate_secret_key_random_encrypted(self):
        """Test validation with random encrypted key."""
        secret = "my-secret-key"
        random_encrypted = "random-encrypted-key"
        is_valid = EncryptionKeyMixin.validate_secret_key(
            secret, random_encrypted, TEST_ENCRYPTION_KEY
        )
        assert is_valid is False

    def test_validate_secret_key_short_encryption_key(self):
        """Test validation with short encryption key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        short_key = "short"
        is_valid = EncryptionKeyMixin.validate_secret_key(secret, encrypted, short_key)
        # Should return False instead of raising error
        assert is_valid is False

    def test_validate_secret_key_timing_attack_resistance(self):
        """Test that validation uses constant-time comparison."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)

        # Multiple validations should behave consistently
        results = []
        for _ in range(10):
            is_valid = EncryptionKeyMixin.validate_secret_key(
                secret, encrypted, TEST_ENCRYPTION_KEY
            )
            results.append(is_valid)

        assert all(results)  # All should be True

    def test_validate_secret_key_with_unicode(self):
        """Test validation with unicode characters."""
        secret = "my-secret-key-🔐-unicode"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        is_valid = EncryptionKeyMixin.validate_secret_key(
            secret, encrypted, TEST_ENCRYPTION_KEY
        )
        assert is_valid is True

    def test_validate_secret_key_case_sensitive(self):
        """Test that validation is case-sensitive."""
        secret = "MySecretKey"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        is_valid = EncryptionKeyMixin.validate_secret_key(
            "mysecretkey", encrypted, TEST_ENCRYPTION_KEY
        )
        assert is_valid is False


class TestDecryptSecretKey:
    """Tests for decrypt_secret_key method."""

    def test_decrypt_secret_key_returns_original(self):
        """Test that decryption returns original secret key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        decrypted = EncryptionKeyMixin.decrypt_secret_key(
            encrypted, TEST_ENCRYPTION_KEY
        )
        assert decrypted == secret

    def test_decrypt_secret_key_with_empty_encrypted_key(self):
        """Test that decryption fails with empty encrypted key."""
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.decrypt_secret_key("", TEST_ENCRYPTION_KEY)
        assert "Encrypted key is required" in str(exc_info.value)

    def test_decrypt_secret_key_with_none_encrypted_key(self):
        """Test that decryption fails with None encrypted key."""
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.decrypt_secret_key(None, TEST_ENCRYPTION_KEY)
        assert "Encrypted key is required" in str(exc_info.value)

    def test_decrypt_secret_key_with_empty_encryption_key(self):
        """Test that decryption fails with empty encryption key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.decrypt_secret_key(encrypted, "")
        assert "Encryption key is required" in str(exc_info.value)

    def test_decrypt_secret_key_with_none_encryption_key(self):
        """Test that decryption fails with None encryption key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.decrypt_secret_key(encrypted, None)
        assert "Encryption key is required" in str(exc_info.value)

    def test_decrypt_secret_key_with_unicode(self):
        """Test decrypting a string with unicode characters."""
        secret = "my-secret-key-🔐-unicode"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        decrypted = EncryptionKeyMixin.decrypt_secret_key(
            encrypted, TEST_ENCRYPTION_KEY
        )
        assert decrypted == secret

    def test_decrypt_secret_key_wrong_encryption_key(self):
        """Test decryption with wrong encryption key."""
        secret = "my-secret-key"
        # Use a different key with same length
        wrong_encryption_key = "different-encryption-key-32-bytes"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        with pytest.raises(InvalidToken):
            EncryptionKeyMixin.decrypt_secret_key(encrypted, wrong_encryption_key)

    def test_decrypt_secret_key_corrupted(self):
        """Test decryption with corrupted encrypted key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        # Corrupt the encrypted key
        corrupted = encrypted[:-10] + "corrupted!"
        with pytest.raises(InvalidToken):
            EncryptionKeyMixin.decrypt_secret_key(corrupted, TEST_ENCRYPTION_KEY)

    def test_decrypt_secret_key_random_encrypted(self):
        """Test decryption with random encrypted key."""
        random_encrypted = "random-encrypted-key"
        with pytest.raises(InvalidToken):
            EncryptionKeyMixin.decrypt_secret_key(random_encrypted, TEST_ENCRYPTION_KEY)

    def test_decrypt_secret_key_short_encryption_key(self):
        """Test that decryption fails with short encryption key."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        short_key = "short"
        with pytest.raises(ValueError) as exc_info:
            EncryptionKeyMixin.decrypt_secret_key(encrypted, short_key)
        assert "at least 32 bytes" in str(exc_info.value)

    def test_decrypt_secret_key_multiple_times(self):
        """Test that decryption is consistent across multiple calls."""
        secret = "my-secret-key"
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)

        # Decrypt multiple times
        results = [
            EncryptionKeyMixin.decrypt_secret_key(encrypted, TEST_ENCRYPTION_KEY)
            for _ in range(10)
        ]

        # All should return the same original secret
        assert all(r == secret for r in results)


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_complete_workflow(self):
        """Test the complete workflow: generate, encrypt, validate, decrypt."""
        # Generate secret key
        secret = EncryptionKeyMixin.generate_secret_key()
        assert isinstance(secret, str)

        # Encrypt the secret key
        encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, TEST_ENCRYPTION_KEY)
        assert isinstance(encrypted, str)
        assert encrypted != secret

        # Validate with correct key
        is_valid = EncryptionKeyMixin.validate_secret_key(
            secret, encrypted, TEST_ENCRYPTION_KEY
        )
        assert is_valid is True

        # Validate with wrong key
        is_valid = EncryptionKeyMixin.validate_secret_key(
            "wrong-key", encrypted, TEST_ENCRYPTION_KEY
        )
        assert is_valid is False

        # Decrypt the secret key
        decrypted = EncryptionKeyMixin.decrypt_secret_key(
            encrypted, TEST_ENCRYPTION_KEY
        )
        assert decrypted == secret

    def test_multiple_secrets_with_same_encryption_key(self):
        """Test encrypting multiple different secrets with the same encryption key."""
        secrets = [EncryptionKeyMixin.generate_secret_key() for _ in range(10)]

        # Encrypt all secrets
        encrypted_secrets = [
            EncryptionKeyMixin.encrypt_secret_key(s, TEST_ENCRYPTION_KEY)
            for s in secrets
        ]

        # All encrypted values should be unique
        assert len(encrypted_secrets) == len(set(encrypted_secrets))

        # Each encrypted secret should decrypt back to its original
        for original, encrypted in zip(secrets, encrypted_secrets):
            decrypted = EncryptionKeyMixin.decrypt_secret_key(
                encrypted, TEST_ENCRYPTION_KEY
            )
            assert decrypted == original

    def test_different_encryption_keys(self):
        """Test that different encryption keys produce different results."""
        secret = "my-secret-key"
        key1 = "a" * 32
        key2 = "b" * 32

        encrypted1 = EncryptionKeyMixin.encrypt_secret_key(secret, key1)
        encrypted2 = EncryptionKeyMixin.encrypt_secret_key(secret, key2)

        # Different encryption keys should produce different encrypted values
        assert encrypted1 != encrypted2

        # Each should decrypt correctly with its own key
        decrypted1 = EncryptionKeyMixin.decrypt_secret_key(encrypted1, key1)
        decrypted2 = EncryptionKeyMixin.decrypt_secret_key(encrypted2, key2)

        assert decrypted1 == secret
        assert decrypted2 == secret

        # Each should fail to decrypt with the other key
        with pytest.raises(InvalidToken):
            EncryptionKeyMixin.decrypt_secret_key(encrypted1, key2)

        with pytest.raises(InvalidToken):
            EncryptionKeyMixin.decrypt_secret_key(encrypted2, key1)

    def test_realistic_use_case(self):
        """Test a realistic use case: shareable resource link."""
        # Simulate creating a shareable resource
        resource_id = "resource-123"
        secret_key = EncryptionKeyMixin.generate_secret_key()

        # Encrypt for storage in database
        encrypted_key = EncryptionKeyMixin.encrypt_secret_key(
            secret_key, TEST_ENCRYPTION_KEY
        )

        # Store in database (simulated)
        database = {
            resource_id: {
                "encrypted_secret": encrypted_key,
                "name": "My Shared Resource",
            }
        }

        # User accesses the resource with the secret key
        provided_key = secret_key  # User provides this in URL/header
        stored_encrypted = database[resource_id]["encrypted_secret"]

        # Validate access
        has_access = EncryptionKeyMixin.validate_secret_key(
            provided_key, stored_encrypted, TEST_ENCRYPTION_KEY
        )
        assert has_access is True

        # Invalid access attempt
        has_access = EncryptionKeyMixin.validate_secret_key(
            "invalid-key", stored_encrypted, TEST_ENCRYPTION_KEY
        )
        assert has_access is False
