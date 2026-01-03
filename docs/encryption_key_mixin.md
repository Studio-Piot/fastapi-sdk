# EncryptionKeyMixin

The `EncryptionKeyMixin` provides a reusable set of methods for managing secret keys with encryption. It's designed for scenarios where you need to provide secure, token-based access to specific resources via public endpoints.

## Overview

This mixin enables controllers to:
- Generate cryptographically secure random secret keys
- Encrypt secret keys before storing them in a database
- Validate provided keys against stored encrypted values
- Decrypt encrypted keys when needed

## Use Cases

Common scenarios where this mixin is useful:

1. **Shareable Resource Links**: Generate unique secret keys for shareable links to private resources
2. **API Access Tokens**: Create resource-specific access tokens
3. **Temporary Access**: Provide time-limited access to specific resources
4. **Public Endpoint Security**: Secure public endpoints that should only be accessible with a valid secret

## Security Features

- **Fernet Symmetric Encryption**: Uses cryptography library's Fernet implementation
- **Cryptographically Secure Random**: Uses `secrets.token_urlsafe()` for key generation
- **Timing Attack Resistance**: Uses `secrets.compare_digest()` for constant-time comparison
- **URL-Safe Keys**: Generated keys are URL-safe and can be used in query parameters or headers

## Installation

The mixin is part of the `fastapi-sdk` package. Make sure you have the required dependencies:

```bash
pip install fastapi-sdk
```

Or if using uv:

```bash
uv pip install fastapi-sdk
```

## Basic Usage

### 1. Import and Use in Your Controller

```python
from fastapi_sdk.controllers.mixin import EncryptionKeyMixin
from api.config import settings

class MyResourceController(EncryptionKeyMixin):
    """Controller with encryption key management capabilities."""
    
    def create_shareable_link(self, resource_id: str):
        # Generate a new secret key
        secret_key = self.generate_secret_key()
        
        # Encrypt the key before storing
        encrypted_key = self.encrypt_secret_key(
            secret_key,
            settings.SECRET_ENCRYPTION_KEY
        )
        
        # Store encrypted key in database
        # (Your database logic here)
        
        # Return the plain secret key to user (only shown once)
        return {
            "resource_id": resource_id,
            "secret_key": secret_key,
            "share_url": f"https://example.com/share/{resource_id}?key={secret_key}"
        }
    
    def validate_access(self, resource_id: str, provided_key: str):
        # Fetch encrypted key from database
        # encrypted_key = db.get_resource_secret(resource_id)
        
        # Validate the provided key
        is_valid = self.validate_secret_key(
            provided_key,
            encrypted_key,
            settings.SECRET_ENCRYPTION_KEY
        )
        
        if not is_valid:
            raise HTTPException(status_code=403, detail="Invalid secret key")
        
        # Proceed with resource access
        return get_resource(resource_id)
```

### 2. Configure Encryption Key

The mixin requires an encryption key that must be:
- At least 32 bytes long
- Stored securely (environment variables or secrets manager)
- Never exposed to end users

**Generate a secure encryption key:**

```bash
# Using OpenSSL (recommended)
openssl rand -hex 32

# Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Example configuration:

```python
# api/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_ENCRYPTION_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

```bash
# .env
SECRET_ENCRYPTION_KEY=your-32-byte-or-longer-encryption-key-here
```

## API Reference

### `generate_secret_key() -> str`

Generate a cryptographically secure random secret key.

Uses `secrets.token_urlsafe(32)` to generate 32 bytes (256 bits) of cryptographically secure random data. The collision probability is negligible - you would need to generate approximately 2^128 (3.4 × 10^38) keys before having a 50% chance of a single collision.

**Returns:**
- `str`: A URL-safe random string (43 characters, 32 bytes of entropy)

**Example:**
```python
secret = EncryptionKeyMixin.generate_secret_key()
# Output: 'kJ8F3mN9pQ2rT7vW1xY4zA6bC8dE0fG2hI5jK7lM9nO'
```

**Note:** No collision detection is needed - the 256-bit entropy provides the same security level as AES-256 encryption keys and Bitcoin private keys.

---

### `encrypt_secret_key(secret_key: str, encryption_key: str) -> str`

Encrypt a secret key using Fernet symmetric encryption.

**Parameters:**
- `secret_key` (str): The plain text secret key to encrypt
- `encryption_key` (str): The encryption key (must be at least 32 bytes)

**Returns:**
- `str`: The encrypted secret key as a base64-encoded string

**Raises:**
- `ValueError`: If encryption_key is less than 32 bytes

**Example:**
```python
secret = "my-secret-key"
encrypted = EncryptionKeyMixin.encrypt_secret_key(
    secret,
    settings.SECRET_ENCRYPTION_KEY
)
```

---

### `validate_secret_key(provided_key: str, encrypted_key: str, encryption_key: str) -> bool`

Validate a provided secret key against the stored encrypted value.

**Parameters:**
- `provided_key` (str): The plain text key provided by the user
- `encrypted_key` (str): The encrypted key stored in the database
- `encryption_key` (str): The encryption key used to decrypt

**Returns:**
- `bool`: True if the provided key matches, False otherwise

**Example:**
```python
is_valid = EncryptionKeyMixin.validate_secret_key(
    user_provided_key,
    stored_encrypted_key,
    settings.SECRET_ENCRYPTION_KEY
)

if not is_valid:
    raise HTTPException(status_code=403, detail="Invalid key")
```

---

### `decrypt_secret_key(encrypted_key: str, encryption_key: str) -> str`

Decrypt an encrypted secret key.

**Parameters:**
- `encrypted_key` (str): The encrypted key to decrypt
- `encryption_key` (str): The encryption key used to decrypt

**Returns:**
- `str`: The decrypted plain text secret key

**Raises:**
- `ValueError`: If encryption_key is less than 32 bytes
- `InvalidToken`: If the encrypted_key is invalid or corrupted

**Example:**
```python
from cryptography.fernet import InvalidToken

try:
    decrypted = EncryptionKeyMixin.decrypt_secret_key(
        encrypted_key,
        settings.SECRET_ENCRYPTION_KEY
    )
except InvalidToken:
    # Handle invalid or corrupted key
    pass
```

## Complete Example: Shareable Resource System

Here's a complete example implementing a shareable resource system:

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi_sdk.controllers.mixin import EncryptionKeyMixin
from pydantic import BaseModel
from api.config import settings
from api.database import db

app = FastAPI()

class ShareableResource(BaseModel):
    id: str
    name: str
    content: str
    encrypted_secret: str | None = None

class ShareResponse(BaseModel):
    resource_id: str
    secret_key: str
    share_url: str

class ResourceController(EncryptionKeyMixin):
    """Controller for managing shareable resources."""
    
    async def create_share_link(self, resource_id: str) -> ShareResponse:
        """Create a shareable link for a resource."""
        # Check if resource exists
        resource = await db.get_resource(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Generate and encrypt secret key
        secret_key = self.generate_secret_key()
        encrypted_key = self.encrypt_secret_key(
            secret_key,
            settings.SECRET_ENCRYPTION_KEY
        )
        
        # Update resource with encrypted secret
        await db.update_resource(
            resource_id,
            {"encrypted_secret": encrypted_key}
        )
        
        # Return share information (secret_key shown only once)
        return ShareResponse(
            resource_id=resource_id,
            secret_key=secret_key,
            share_url=f"https://api.example.com/share/{resource_id}?key={secret_key}"
        )
    
    async def access_shared_resource(
        self,
        resource_id: str,
        secret_key: str
    ) -> ShareableResource:
        """Access a shared resource using secret key."""
        # Fetch resource from database
        resource = await db.get_resource(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Check if resource has a secret
        if not resource.encrypted_secret:
            raise HTTPException(
                status_code=403,
                detail="Resource is not shared"
            )
        
        # Validate the provided secret key
        is_valid = self.validate_secret_key(
            secret_key,
            resource.encrypted_secret,
            settings.SECRET_ENCRYPTION_KEY
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=403,
                detail="Invalid or expired secret key"
            )
        
        # Return the resource
        return resource
    
    async def revoke_share_link(self, resource_id: str):
        """Revoke a share link by removing the encrypted secret."""
        await db.update_resource(
            resource_id,
            {"encrypted_secret": None}
        )

# Initialize controller
controller = ResourceController()

# Routes
@app.post("/resources/{resource_id}/share", response_model=ShareResponse)
async def create_share_link(resource_id: str):
    """Create a shareable link for a resource."""
    return await controller.create_share_link(resource_id)

@app.get("/share/{resource_id}", response_model=ShareableResource)
async def access_shared_resource(resource_id: str, key: str):
    """Access a shared resource using its secret key."""
    return await controller.access_shared_resource(resource_id, key)

@app.delete("/resources/{resource_id}/share")
async def revoke_share_link(resource_id: str):
    """Revoke a share link."""
    await controller.revoke_share_link(resource_id)
    return {"message": "Share link revoked"}
```

## Database Schema Example

Example MongoDB/Odmantic model:

```python
from odmantic import Model, Field
from typing import Optional

class Resource(Model):
    name: str
    content: str
    encrypted_secret: Optional[str] = Field(default=None)
    owner_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        collection = "resources"
```

## Security Best Practices

1. **Store Encryption Key Securely**
   - Use environment variables or a secrets manager
   - Never commit encryption keys to version control
   - Rotate encryption keys periodically

2. **Secret Key Handling**
   - Only show the plain secret key once (when generated)
   - Never log secret keys
   - Consider adding expiration to secrets

3. **Validation**
   - Always validate secret keys before granting access
   - Use the built-in `validate_secret_key()` method for timing-attack resistance
   - Consider rate limiting validation attempts

4. **Database Security**
   - Store only encrypted values in the database
   - Use appropriate database access controls
   - Consider adding indexes on resource IDs for performance

5. **HTTPS Only**
   - Always use HTTPS in production
   - Secret keys in URLs should only be transmitted over secure connections

## Testing

The mixin includes comprehensive unit tests. To run them:

```bash
pytest tests/controllers/test_mixin.py -v
```

Example test:

```python
from fastapi_sdk.controllers.mixin import EncryptionKeyMixin

def test_encryption_workflow():
    encryption_key = "my-32-byte-encryption-key-here!!"
    
    # Generate secret
    secret = EncryptionKeyMixin.generate_secret_key()
    
    # Encrypt
    encrypted = EncryptionKeyMixin.encrypt_secret_key(secret, encryption_key)
    
    # Validate
    assert EncryptionKeyMixin.validate_secret_key(
        secret, encrypted, encryption_key
    )
    
    # Decrypt
    decrypted = EncryptionKeyMixin.decrypt_secret_key(encrypted, encryption_key)
    assert decrypted == secret
```

## Migration Guide

If you're migrating from a version that used hardcoded settings import:

### Old Code (v0.11.1 and earlier)
```python
# Won't work in reusable contexts
encrypted = self.encrypt_secret_key(secret_key)
is_valid = self.validate_secret_key(provided_key, encrypted_key)
decrypted = self.decrypt_secret_key(encrypted_key)
```

### New Code (v0.11.2+)
```python
# Pass encryption_key as parameter
from api.config import settings

encrypted = self.encrypt_secret_key(
    secret_key,
    settings.SECRET_ENCRYPTION_KEY
)

is_valid = self.validate_secret_key(
    provided_key,
    encrypted_key,
    settings.SECRET_ENCRYPTION_KEY
)

decrypted = self.decrypt_secret_key(
    encrypted_key,
    settings.SECRET_ENCRYPTION_KEY
)
```

## Troubleshooting

### ValueError: Encryption key must be at least 32 bytes long

**Cause**: The encryption key is shorter than 32 bytes.

**Solution**: Ensure your `SECRET_ENCRYPTION_KEY` is at least 32 characters. Generate a secure key using:

```bash
# Using OpenSSL (recommended)
openssl rand -hex 32

# Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### InvalidToken Exception

**Cause**: The encrypted key is corrupted, or you're using a different encryption key.

**Solution**: 
- Verify you're using the same encryption key for encrypt/decrypt
- Check that the encrypted value wasn't modified
- Ensure the encryption key hasn't changed

### Validation Always Returns False

**Cause**: Wrong secret key, wrong encryption key, or corrupted data.

**Solution**:
- Verify the provided key matches the original
- Ensure the encryption key is correct
- Check database for data corruption

## Related Documentation

- [Model Controller](./model_controller.md)
- [Route Controller](./route_controller.md)
- [Webhook Security](./webhook.md)

## Support

For issues or questions:
- GitHub Issues: [fastapi-sdk issues](https://github.com/studio-piot/fastapi-sdk/issues)
- Documentation: [FastAPI SDK Docs](https://github.com/studio-piot/fastapi-sdk/docs)

