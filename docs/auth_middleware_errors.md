# Authentication Middleware Error Responses

This document describes all error responses that can be returned by the `AuthMiddleware` when authentication fails. All authentication errors return HTTP status code `401 Unauthorized`.

## Error Response Format

All authentication errors follow the standard response format:

```json
{
  "status": {
    "code": 401,
    "message": "Unauthorized"
  },
  "data": null,
  "errors": [
    {
      "code": "ERROR_CODE",
      "message": "Human-readable error message"
    }
  ],
  "meta": {
    "timestamp": "2025-01-15T10:30:00.000Z",
    "request_id": "req-abc123"
  }
}
```

## Error Types

### 1. MISSING_AUTH_HEADER

**When it occurs:** The request is missing the `Authorization` header or the header doesn't start with `Bearer `.

**Error Code:** `MISSING_AUTH_HEADER`

**Example Response:**

```json
{
  "status": {
    "code": 401,
    "message": "Unauthorized"
  },
  "data": null,
  "errors": [
    {
      "code": "MISSING_AUTH_HEADER",
      "message": "Missing or invalid Authorization header"
    }
  ],
  "meta": {
    "timestamp": "2025-01-15T10:30:00.000Z",
    "request_id": "req-abc123"
  }
}
```

**Recommended Handling:**
- Prompt the user to log in
- Redirect to the login page
- Show an authentication required message

---

### 2. TOKEN_EXPIRED

**When it occurs:** The JWT token has expired (past its `exp` claim).

**Error Code:** `TOKEN_EXPIRED`

**Example Response:**

```json
{
  "status": {
    "code": 401,
    "message": "Unauthorized"
  },
  "data": null,
  "errors": [
    {
      "code": "TOKEN_EXPIRED",
      "message": "Token has expired"
    }
  ],
  "meta": {
    "timestamp": "2025-01-15T10:30:00.000Z",
    "request_id": "req-abc123"
  }
}
```

**Recommended Handling:**
- Attempt to refresh the access token using the refresh token
- If refresh fails, redirect to login
- Show a "Session expired" message

---

### 3. TOKEN_INVALID_SIGNATURE

**When it occurs:** The JWT token signature is invalid or has been tampered with.

**Error Code:** `TOKEN_INVALID_SIGNATURE`

**Example Response:**

```json
{
  "status": {
    "code": 401,
    "message": "Unauthorized"
  },
  "data": null,
  "errors": [
    {
      "code": "TOKEN_INVALID_SIGNATURE",
      "message": "Invalid token signature"
    }
  ],
  "meta": {
    "timestamp": "2025-01-15T10:30:00.000Z",
    "request_id": "req-abc123"
  }
}
```

**Recommended Handling:**
- Clear stored tokens
- Logout the user
- Redirect to login page
- Show a "Invalid session" message

---

### 4. TOKEN_INVALID_CLAIM

**When it occurs:** The JWT token has an invalid claim, such as a wrong issuer (`iss` claim doesn't match the expected issuer).

**Error Code:** `TOKEN_INVALID_CLAIM`

**Example Response:**

```json
{
  "status": {
    "code": 401,
    "message": "Unauthorized"
  },
  "data": null,
  "errors": [
    {
      "code": "TOKEN_INVALID_CLAIM",
      "message": "Invalid token claim: Invalid issuer"
    }
  ],
  "meta": {
    "timestamp": "2025-01-15T10:30:00.000Z",
    "request_id": "req-abc123"
  }
}
```

**Recommended Handling:**
- Clear stored tokens
- Logout the user
- Redirect to login page
- Show a "Invalid token" message

---

### 5. TOKEN_VERIFICATION_FAILED

**When it occurs:** Token verification fails for other reasons, such as:
- Wrong `tenant_id` (doesn't match `auth_client_id`)
- Malformed token
- Other verification failures

**Error Code:** `TOKEN_VERIFICATION_FAILED`

**Example Response (Wrong tenant_id):**

```json
{
  "status": {
    "code": 401,
    "message": "Unauthorized"
  },
  "data": null,
  "errors": [
    {
      "code": "TOKEN_VERIFICATION_FAILED",
      "message": "Token tenant_id does not match auth_client_id"
    }
  ],
  "meta": {
    "timestamp": "2025-01-15T10:30:00.000Z",
    "request_id": "req-abc123"
  }
}
```

**Example Response (Malformed token):**

```json
{
  "status": {
    "code": 401,
    "message": "Unauthorized"
  },
  "data": null,
  "errors": [
    {
      "code": "TOKEN_VERIFICATION_FAILED",
      "message": "Token verification failed: Invalid token format"
    }
  ],
  "meta": {
    "timestamp": "2025-01-15T10:30:00.000Z",
    "request_id": "req-abc123"
  }
}
```

**Recommended Handling:**
- Clear stored tokens
- Logout the user
- Redirect to login page
- Show an appropriate error message based on the specific error message

---

## Client-Side Error Handling Example

Here's an example of how to handle these errors in your application:

```typescript
// TypeScript/JavaScript example
interface AuthError {
  code: string;
  message: string;
}

interface ErrorResponse {
  status: {
    code: number;
    message: string;
  };
  errors: AuthError[];
  meta: {
    timestamp: string;
    request_id?: string;
  };
}

async function handleAuthError(response: Response): Promise<void> {
  const errorData: ErrorResponse = await response.json();
  const errorCode = errorData.errors[0]?.code;

  switch (errorCode) {
    case 'MISSING_AUTH_HEADER':
      // Redirect to login
      window.location.href = '/login';
      break;

    case 'TOKEN_EXPIRED':
      // Try to refresh the token
      const refreshed = await refreshAccessToken();
      if (!refreshed) {
        // If refresh fails, redirect to login
        window.location.href = '/login';
      }
      break;

    case 'TOKEN_INVALID_SIGNATURE':
    case 'TOKEN_INVALID_CLAIM':
    case 'TOKEN_VERIFICATION_FAILED':
      // Clear tokens and logout
      clearStoredTokens();
      window.location.href = '/login';
      break;

    default:
      // Unknown error, redirect to login
      window.location.href = '/login';
  }
}
```

```python
# Python example
from enum import Enum

class AuthErrorCode(str, Enum):
    MISSING_AUTH_HEADER = "MISSING_AUTH_HEADER"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID_SIGNATURE = "TOKEN_INVALID_SIGNATURE"
    TOKEN_INVALID_CLAIM = "TOKEN_INVALID_CLAIM"
    TOKEN_VERIFICATION_FAILED = "TOKEN_VERIFICATION_FAILED"

def handle_auth_error(error_response: dict) -> None:
    """Handle authentication errors from the API."""
    error_code = error_response.get("errors", [{}])[0].get("code")
    
    if error_code == AuthErrorCode.MISSING_AUTH_HEADER:
        # Redirect to login
        redirect_to_login()
    
    elif error_code == AuthErrorCode.TOKEN_EXPIRED:
        # Try to refresh the token
        if not refresh_access_token():
            redirect_to_login()
    
    elif error_code in [
        AuthErrorCode.TOKEN_INVALID_SIGNATURE,
        AuthErrorCode.TOKEN_INVALID_CLAIM,
        AuthErrorCode.TOKEN_VERIFICATION_FAILED,
    ]:
        # Clear tokens and logout
        clear_stored_tokens()
        redirect_to_login()
    
    else:
        # Unknown error, redirect to login
        redirect_to_login()
```

---

## Summary Table

| Error Code | HTTP Status | When It Occurs | Recommended Action |
|------------|-------------|----------------|-------------------|
| `MISSING_AUTH_HEADER` | 401 | No Authorization header or invalid format | Redirect to login |
| `TOKEN_EXPIRED` | 401 | Token has expired | Try to refresh token, then redirect to login if refresh fails |
| `TOKEN_INVALID_SIGNATURE` | 401 | Token signature is invalid | Clear tokens and redirect to login |
| `TOKEN_INVALID_CLAIM` | 401 | Token has invalid claim (e.g., wrong issuer) | Clear tokens and redirect to login |
| `TOKEN_VERIFICATION_FAILED` | 401 | Other verification failures (wrong tenant_id, malformed token, etc.) | Clear tokens and redirect to login |

---

## Notes

- All authentication errors return HTTP status code `401 Unauthorized`
- The `request_id` in the `meta` field can be used for debugging and support requests
- The `timestamp` field indicates when the error occurred
- Always check the `code` field in the `errors` array to determine the specific error type
- The `message` field provides human-readable error details

