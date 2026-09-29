# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.12.17] - 2026-09-29

### Added

- `register_exception_handlers(app, debug=True)` logs every error response (method, path, status, JSON body) to the `fastapi_sdk.errors` logger.
- The debug log masks sensitive values (`password`, `secret`, `token`, `api_key`, `card_number`, `cvv`, `cvc`, including nested keys) as `"***"`. Responses are not masked. The list is set through `register_exception_handlers(app, sensitive_fields=...)`.

### Fixed

- 422 responses now return the submitted payload in `data` when a controller raises a pydantic `ValidationError`. Previously `data` was `null`.
- Form submissions that fail validation now return a 422 with the form fields in `data`. Previously they caused a 500 because `FormData` is not JSON serializable.

## [0.12.16] - 2026-09-26

### Added

- `configure_role_permissions` maps a role to a fixed permission list. `require_permission` and `require_combined_permission` both consult it. `superuser` still grants every permission. Token claims are left unchanged.

## [0.12.13] - 2026-08-05

### Changed

- Replaced deprecated `authlib.jose` with `joserfc` for JWT encode/decode to clear Authlib deprecation warnings

## [0.12.12] - 2026-07-23

### Changed

- Clarified models vs schemas in docs: `schemas.md` is the canonical schema guide; `route_controller.md` links to it and no longer duplicates schema definitions

## [0.12.11] - 2026-07-23

### Changed

- Reorganised README documentation links to cover all docs under `docs/`, using absolute GitHub URLs so they work on PyPI

## [0.12.10] - 2026-07-23

### Added

- Exception handler for Pydantic `ValidationError`, using the same 422 response format as `RequestValidationError`
