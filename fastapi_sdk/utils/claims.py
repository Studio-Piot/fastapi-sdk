"""Helpers for reading user identity out of JWT claims.

`AuthMiddleware` attaches the decoded token payload to `request.state.claims`,
so reading identity means reaching into a plain dict. These helpers do that
consistently and never raise, which matters because the usual call site is a
controller hook writing an audit record — a missing claim should leave a blank
name, not abort the write.

The claim names follow the auth provider's token format: `sub` for the user id,
and `user_first_name` / `user_last_name` / `user_email` for display.
"""

from typing import Any, Dict, Optional


def claims_user_id(claims: Optional[Dict[str, Any]]) -> str:
    """Return the user id from the claims, or an empty string.

    Args:
        claims: The claims dict from the JWT token, or None

    Returns:
        The `sub` claim, or an empty string when it is absent
    """
    if not claims:
        return ""
    return claims.get("sub", "")


def claims_user_name(claims: Optional[Dict[str, Any]]) -> str:
    """Return a display name for the caller, or an empty string.

    Joins the first and last name claims, skipping whichever is missing so the
    result carries no stray whitespace. Falls back to the email when no name
    parts are present, so a stored audit entry still identifies someone.

    Args:
        claims: The claims dict from the JWT token, or None

    Returns:
        The caller's display name, their email, or an empty string
    """
    if not claims:
        return ""

    parts = [
        claims.get("user_first_name", ""),
        claims.get("user_last_name", ""),
    ]
    name = " ".join(part for part in parts if part).strip()

    return name or claims.get("user_email", "")
