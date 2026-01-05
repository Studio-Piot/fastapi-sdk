# Response format

Define a global format, as pure JSON Schema object, of how all response should be formatted.

## JSON Schema

```json
{
  "$id": "https://example.com/schemas/standard-response.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "StandardResponse",
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": {
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "code": {
          "type": "integer",
          "description": "HTTP status code (e.g., 200, 400, 500)"
        },
        "message": {
          "type": "string",
          "description": "Short status message, e.g., 'OK', 'Bad Request'"
        }
      },
      "additionalProperties": false
    },
    "data": {
      "description": "Main payload on success; null on most errors; may contain original submitted data on validation errors (422)",
      "type": ["object", "array", "null"],
      "additionalProperties": true
    },
    "errors": {
      "description": "List of errors when the request fails; null or omitted on success",
      "type": ["array", "null"],
      "items": {
        "$ref": "#/$defs/Error"
      }
    },
    "meta": {
      "description": "Additional metadata (pagination, request_id, timestamps, etc.)",
      "type": ["object", "null"],
      "additionalProperties": true
    }
  },
  "additionalProperties": false,
  "$defs": {
    "Error": {
      "title": "Error",
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "field": {
          "type": ["string", "null"],
          "description": "Optional field name related to the error (for validation errors)"
        },
        "code": {
          "type": "string",
          "description": "Machine-readable error code (e.g., 'INVALID_FORMAT')"
        },
        "message": {
          "type": "string",
          "description": "Human-readable error description"
        }
      },
      "additionalProperties": false
    }
  }
}
```

## Example JSON responses

### 200 OK — Success Response

Example (returning a User object)

```json
{
  "status": {
    "code": 200,
    "message": "OK"
  },
  "data": {
    "uuid": "usr_abc123",
    "email": "user@example.com",
    "name": "Jane Doe",
    "created_at": "2025-11-24T10:15:00Z"
  },
  "errors": null,
  "meta": {
    "timestamp": "2025-11-24T10:30:00Z",
    "request_id": "req-789"
  }
}
```

### 200 OK — Success Response with Pagination

Example (returning a list of Users with pagination metadata)

```json
{
  "status": {
    "code": 200,
    "message": "OK"
  },
  "data": [
    {
      "uuid": "usr_abc123",
      "email": "user1@example.com",
      "name": "Jane Doe",
      "created_at": "2025-11-24T10:15:00Z"
    },
    {
      "uuid": "usr_def456",
      "email": "user2@example.com",
      "name": "John Smith",
      "created_at": "2025-11-24T10:16:00Z"
    },
    {
      "uuid": "usr_ghi789",
      "email": "user3@example.com",
      "name": "Alice Johnson",
      "created_at": "2025-11-24T10:17:00Z"
    }
  ],
  "errors": null,
  "meta": {
    "timestamp": "2025-11-24T10:30:00Z",
    "request_id": "req-789",
    "total": 47,
    "page": 1,
    "pages": 5,
    "size": 10
  }
}
```

### ⚠️ 400 Bad Request — Validation / Client Error

Example (missing or invalid fields)

```json
{
  "status": {
    "code": 400,
    "message": "Bad Request"
  },
  "data": null,
  "errors": [
    {
      "field": "email",
      "code": "INVALID_FORMAT",
      "message": "The email address provided is not valid."
    },
    {
      "field": "password",
      "code": "TOO_SHORT",
      "message": "Password must contain at least 8 characters."
    }
  ],
  "meta": {
    "timestamp": "2025-11-24T10:31:00Z",
    "request_id": "req-790"
  }
}
```

### ⚠️ 422 Unprocessable Entity — Validation Error

Example (Pydantic validation errors with original payload)

```json
{
  "status": {
    "code": 422,
    "message": "Unprocessable Entity"
  },
  "data": {
    "email": "invalid-email",
    "name": "John Doe",
    "age": "not-a-number"
  },
  "errors": [
    {
      "field": "email",
      "code": "INVALID_FORMAT",
      "message": "value is not a valid email address"
    },
    {
      "field": "age",
      "code": "INVALID_TYPE",
      "message": "value is not a valid integer"
    }
  ],
  "meta": {
    "timestamp": "2025-11-24T10:31:30Z",
    "request_id": "req-792"
  }
}
```

**Note:** For validation errors (422), the `data` field contains the original payload that was submitted, making it easier to debug and provide user feedback.

### 💥 500 Internal Server Error — Unexpected Failure

Example (generic safe message)

```json
{
  "status": {
    "code": 500,
    "message": "Internal Server Error"
  },
  "data": null,
  "errors": [
    {
      "field": null,
      "code": "UNEXPECTED_ERROR",
      "message": "An unexpected error occurred. Please contact support with the provided request_id."
    }
  ],
  "meta": {
    "timestamp": "2025-11-24T10:32:00Z",
    "request_id": "req-791"
  }
}
```