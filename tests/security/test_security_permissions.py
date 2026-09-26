"""Tests for role grants on permission checks."""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from fastapi_sdk.security.permissions import (
    configure_role_permissions,
    require_combined_permission,
    require_permission,
)


@pytest.fixture(autouse=True)
def reset_role_permissions():
    configure_role_permissions()
    yield
    configure_role_permissions()


def _request(claims: dict) -> SimpleNamespace:
    return SimpleNamespace(state=SimpleNamespace(claims=claims))


def test_token_permission_allows_without_a_role_grant():
    claims = {"permissions": ["activity:read"], "roles": []}

    @require_permission("activity:read")
    async def route(request):
        return "ok"

    assert asyncio.run(route(request=_request(claims))) == "ok"


def test_superuser_allows_every_permission():
    claims = {"roles": ["superuser"]}

    @require_permission("activity:delete")
    async def route(request):
        return "ok"

    assert asyncio.run(route(request=_request(claims))) == "ok"


def test_user_role_denies_until_the_project_configures_it():
    claims = {"roles": ["user"]}

    @require_permission("route:generate")
    async def route(request):
        return "ok"

    with pytest.raises(HTTPException) as exc:
        asyncio.run(route(request=_request(claims)))
    assert exc.value.status_code == 403


def test_configured_user_role_grants_only_its_list_and_leaves_claims_unchanged():
    configure_role_permissions({"user": ["route:generate", "activity:read"]})
    claims = {"roles": ["user"]}

    @require_permission("route:generate")
    async def allowed(request):
        return "ok"

    @require_permission("activity:delete")
    async def denied(request):
        return "ok"

    assert asyncio.run(allowed(request=_request(claims))) == "ok"
    with pytest.raises(HTTPException):
        asyncio.run(denied(request=_request(claims)))
    assert "permissions" not in claims


def test_configure_replaces_previous_grants():
    configure_role_permissions({"user": ["activity:read"]})
    configure_role_permissions({"user": ["activity:create"]})
    user = {"roles": ["user"]}

    @require_permission("activity:read")
    async def read(request):
        return "ok"

    @require_permission("activity:create")
    async def create(request):
        return "ok"

    with pytest.raises(HTTPException):
        asyncio.run(read(request=_request(user)))
    assert asyncio.run(create(request=_request(user))) == "ok"


def test_configure_cannot_narrow_superuser():
    configure_role_permissions({"superuser": ["activity:read"]})
    superuser = {"roles": ["superuser"]}

    @require_permission("activity:delete")
    async def delete(request):
        return "ok"

    assert asyncio.run(delete(request=_request(superuser))) == "ok"


def test_combined_permission_still_runs_the_custom_check():
    configure_role_permissions({"user": ["activity:read"]})
    claims = {"roles": ["user"]}
    seen = {}

    def custom(request, resource_data):
        seen["claims"] = request.state.claims
        seen["resource"] = resource_data
        return resource_data["uuid"] == "act_ok"

    @require_combined_permission("activity:read", custom)
    async def route(request, uuid: str):
        return uuid

    assert asyncio.run(route(request=_request(claims), uuid="act_ok")) == "act_ok"
    assert seen["claims"] is claims
    assert "permissions" not in claims

    with pytest.raises(HTTPException) as exc:
        asyncio.run(route(request=_request(claims), uuid="act_no"))
    assert exc.value.status_code == 403
