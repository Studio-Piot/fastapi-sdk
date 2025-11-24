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
      "description": "Main payload on success; null or omitted on error",
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
    "user_id": "abc123",
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