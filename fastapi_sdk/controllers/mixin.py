"""Mixin for encryption key management.

This mixin provides methods for generating, encrypting, validating, and decrypting
secret keys for secure resource access. It uses Fernet symmetric encryption to
protect secret keys stored in a database.

Typical use case:
    - Generate a secret key for a resource (e.g., a shareable link)
    - Encrypt and store the secret key in the database
    - Allow public endpoint access to the resource using the secret key
    - Validate incoming requests by comparing provided keys with stored encrypted keys

Example usage:
    ```python
    from fastapi_sdk.controllers.mixin import EncryptionKeyMixin
    from api.config import settings

    class MyController(EncryptionKeyMixin):
        def create_shareable_resource(self):
            # Generate a new secret key
            secret_key = self.generate_secret_key()

            # Encrypt before storing in database
            encrypted = self.encrypt_secret_key(
                secret_key,
                settings.SECRET_ENCRYPTION_KEY
            )

            # Store encrypted key in database
            # Return plain secret_key to user (only shown once)
            return secret_key

        def validate_access(self, provided_key: str, stored_encrypted_key: str):
            # Validate provided key against stored encrypted key
            is_valid = self.validate_secret_key(
                provided_key,
                stored_encrypted_key,
                settings.SECRET_ENCRYPTION_KEY
            )
            return is_valid
    ```

Security notes:
    - The encryption key must be at least 32 bytes long
    - Store the encryption key securely (environment variables, secrets manager)
    - Never expose the encryption key or encrypted values to end users
    - Secret keys are generated using cryptographically secure random methods
"""

import base64
import secrets

from cryptography.fernet import Fernet, InvalidToken


class EncryptionKeyMixin:
    """Mixin for encryption key management.

    This mixin provides static methods for managing secret keys with encryption.
    All methods are stateless and thread-safe.
    """

    @staticmethod
    def generate_secret_key() -> str:
        """Generate a cryptographically secure random secret key.

        Uses `secrets.token_urlsafe()` to generate a URL-safe random string
        suitable for use as a secret key for resource access.

        Returns:
            str: A URL-safe random string (43 characters, 32 bytes of entropy)

        Example:
            >>> secret = EncryptionKeyMixin.generate_secret_key()
            >>> len(secret)
            43
            >>> # Example output: 'kJ8F3mN9pQ2rT7vW1xY4zA6bC8dE0fG2hI5jK7lM9nO'
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def encrypt_secret_key(secret_key: str, encryption_key: str) -> str:
        """Encrypt a secret key using Fernet symmetric encryption.

        Args:
            secret_key: The plain text secret key to encrypt
            encryption_key: The encryption key (must be at least 32 bytes)

        Returns:
            str: The encrypted secret key as a base64-encoded string

        Raises:
            ValueError: If encryption_key is less than 32 bytes

        Example:
            >>> secret = "my-secret-key"
            >>> encryption_key = "my-32-byte-encryption-key-here!!"
            >>> encrypted = EncryptionKeyMixin.encrypt_secret_key(
            ...     secret, encryption_key
            ... )
            >>> isinstance(encrypted, str)
            True
        """
        if len(encryption_key) < 32:
            raise ValueError("Encryption key must be at least 32 bytes long")

        key = encryption_key.encode()
        # Fernet key must be 32 url-safe base64-encoded bytes
        fernet_key = base64.urlsafe_b64encode(key[:32])
        f = Fernet(fernet_key)
        return f.encrypt(secret_key.encode()).decode()

    @staticmethod
    def validate_secret_key(
        provided_key: str, encrypted_key: str, encryption_key: str
    ) -> bool:
        """Validate a provided secret key against the stored encrypted value.

        Uses constant-time comparison to prevent timing attacks.

        Args:
            provided_key: The plain text key provided by the user
            encrypted_key: The encrypted key stored in the database
            encryption_key: The encryption key used to decrypt (must be at least 32 bytes)

        Returns:
            bool: True if the provided key matches the decrypted key, False otherwise

        Example:
            >>> secret = "my-secret-key"
            >>> encryption_key = "my-32-byte-encryption-key-here!!"
            >>> encrypted = EncryptionKeyMixin.encrypt_secret_key(
            ...     secret, encryption_key
            ... )
            >>> EncryptionKeyMixin.validate_secret_key(
            ...     secret, encrypted, encryption_key
            ... )
            True
            >>> EncryptionKeyMixin.validate_secret_key(
            ...     "wrong-key", encrypted, encryption_key
            ... )
            False
        """
        if len(encryption_key) < 32:
            return False

        key = encryption_key.encode()
        fernet_key = base64.urlsafe_b64encode(key[:32])
        f = Fernet(fernet_key)
        try:
            decrypted = f.decrypt(encrypted_key.encode()).decode()
            # Use byte comparison for unicode support
            return secrets.compare_digest(
                provided_key.encode("utf-8"), decrypted.encode("utf-8")
            )
        except InvalidToken:
            return False

    @staticmethod
    def decrypt_secret_key(encrypted_key: str, encryption_key: str) -> str:
        """Decrypt an encrypted secret key using Fernet symmetric encryption.

        Args:
            encrypted_key: The encrypted key to decrypt
            encryption_key: The encryption key used to decrypt (must be at least 32 bytes)

        Returns:
            str: The decrypted plain text secret key

        Raises:
            ValueError: If encryption_key is less than 32 bytes
            InvalidToken: If the encrypted_key is invalid or corrupted

        Example:
            >>> secret = "my-secret-key"
            >>> encryption_key = "my-32-byte-encryption-key-here!!"
            >>> encrypted = EncryptionKeyMixin.encrypt_secret_key(
            ...     secret, encryption_key
            ... )
            >>> decrypted = EncryptionKeyMixin.decrypt_secret_key(
            ...     encrypted, encryption_key
            ... )
            >>> decrypted == secret
            True
        """
        if len(encryption_key) < 32:
            raise ValueError("Encryption key must be at least 32 bytes long")

        key = encryption_key.encode()
        fernet_key = base64.urlsafe_b64encode(key[:32])
        f = Fernet(fernet_key)
        return f.decrypt(encrypted_key.encode()).decode()
