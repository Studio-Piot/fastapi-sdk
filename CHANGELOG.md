# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.12.12] - 2026-07-23

### Changed

- Clarified models vs schemas in docs: `schemas.md` is the canonical schema guide; `route_controller.md` links to it and no longer duplicates schema definitions

## [0.12.11] - 2026-07-23

### Changed

- Reorganised README documentation links to cover all docs under `docs/`, using absolute GitHub URLs so they work on PyPI

## [0.12.10] - 2026-07-23

### Added

- Exception handler for Pydantic `ValidationError`, using the same 422 response format as `RequestValidationError`
