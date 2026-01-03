"""Tests for custom permission functionality in RouteController."""

import uuid
from datetime import timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Request

from fastapi_sdk.controllers import RouteController
from fastapi_sdk.utils.test import create_access_token
from tests.config import settings
from tests.controllers import Project
from tests.db import get_db_engine
from tests.schemas import ProjectCreate, ProjectResponse, ProjectUpdate


@pytest.mark.asyncio
class TestCustomPermissions:
    """Test custom permission functionality."""

    def setup_method(self):
        """Reset mocks before each test."""
        # This ensures each test starts with clean mock state
        # Reset any global mocks if they exist
        pass

    def teardown_method(self):
        """Clean up after each test."""
        # Remove any routers that were added during the test
        pass

    @pytest.fixture
    def mock_custom_permission_func(self):
        """Create a mock custom permission function."""
        return AsyncMock(return_value=True)

    @pytest.fixture
    def failing_custom_permission_func(self):
        """Create a mock custom permission function that returns False."""
        return AsyncMock(return_value=False)

    @pytest.fixture
    def custom_permission_func_with_side_effect(self):
        """Create a mock custom permission function with side effects."""
        mock_func = AsyncMock()
        mock_func.side_effect = [
            True,
            False,
            True,
        ]  # First call succeeds, second fails, third succeeds
        return mock_func

    @pytest.fixture
    def auth_headers_with_permissions(self, account):
        """Create headers with JWT token that has project permissions."""
        token = create_access_token(
            test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
            data={
                "sub": "test_user",
                "tenant_id": settings.AUTH_CLIENT_ID,
                "iss": settings.AUTH_ISSUER,
                "account_id": account.uuid,
                "roles": ["user"],
                "permissions": [
                    "project:read",
                    "project:create",
                    "project:update",
                    "project:delete",
                ],
            },
            expires_delta=timedelta(minutes=30),
        )
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def auth_headers_without_permissions(self, account):
        """Create headers with JWT token that has no permissions."""
        token = create_access_token(
            test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
            data={
                "sub": "test_user",
                "tenant_id": settings.AUTH_CLIENT_ID,
                "iss": settings.AUTH_ISSUER,
                "account_id": account.uuid,
                "roles": ["user"],
                "permissions": [],
            },
            expires_delta=timedelta(minutes=30),
        )
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def project_routes_with_custom_permission(self):
        """Create project routes with custom permission function."""
        # Create a fresh mock for each test
        # Use a factory function to ensure each test gets a fresh mock
        mock_func = Mock(return_value=True)
        # Use a unique prefix for each test to avoid router conflicts
        unique_prefix = f"/test-projects-{uuid.uuid4().hex[:8]}"
        return RouteController(
            prefix=unique_prefix,
            tags=["Test Projects"],
            controller=Project,
            get_db=get_db_engine,
            schema_response=ProjectResponse,
            schema_create=ProjectCreate,
            schema_update=ProjectUpdate,
            allowed_query_fields=["account_id", "name"],
            allowed_order_fields=["created_at", "name"],
            custom_permission_func=mock_func,
            custom_permission_error_message="Custom permission denied",
        )

    @pytest.fixture
    def project_routes_with_failing_custom_permission(self):
        """Create project routes with failing custom permission function."""
        # Create a fresh mock for each test
        mock_func = Mock(return_value=False)
        # Use a unique prefix for each test to avoid router conflicts
        unique_prefix = f"/test-projects-failing-{uuid.uuid4().hex[:8]}"
        return RouteController(
            prefix=unique_prefix,
            tags=["Test Projects Failing"],
            controller=Project,
            get_db=get_db_engine,
            schema_response=ProjectResponse,
            schema_create=ProjectCreate,
            schema_update=ProjectUpdate,
            allowed_query_fields=["account_id", "name"],
            allowed_order_fields=["created_at", "name"],
            custom_permission_func=mock_func,
            custom_permission_error_message="Custom permission denied",
        )

    @pytest.fixture
    def project_routes_without_custom_permission(self):
        """Create project routes without custom permission function."""
        return RouteController(
            prefix="/test-projects-no-custom",
            tags=["Test Projects No Custom"],
            controller=Project,
            get_db=get_db_engine,
            schema_response=ProjectResponse,
            schema_create=ProjectCreate,
            schema_update=ProjectUpdate,
            allowed_query_fields=["account_id", "name"],
            allowed_order_fields=["created_at", "name"],
        )

    async def test_custom_permission_function_is_called_on_get(
        self,
        client,
        auth_headers_with_permissions,
        project_routes_with_custom_permission,
        project,
    ):
        """Test that custom permission function is called on GET requests."""
        # Get the mock function from the route controller
        mock_func = project_routes_with_custom_permission.custom_permission_func
        # Reset mock to ensure clean state for this test
        mock_func.reset_mock()

        # Include the router in the app
        client.app.include_router(project_routes_with_custom_permission.router)

        # Make a GET request
        response = client.get(
            f"{project_routes_with_custom_permission.prefix}/{project.uuid}",
            headers=auth_headers_with_permissions,
        )

        # Verify the custom permission function was called
        mock_func.assert_called_once()

        # Verify the function was called with correct arguments
        call_args = mock_func.call_args
        assert len(call_args[0]) == 2  # request and resource_data
        assert isinstance(call_args[0][0], Request)  # First argument should be Request
        assert isinstance(call_args[0][1], dict)  # Second argument should be dict
        assert (
            call_args[0][1]["resource_id"] == project.uuid
        )  # resource_id should be in resource_data

        # Verify the request was successful
        assert response.status_code == 200

    async def test_custom_permission_function_is_called_on_create(
        self,
        client,
        auth_headers_with_permissions,
        project_routes_with_custom_permission,
        account,
    ):
        """Test that custom permission function is called on POST requests."""
        # Get the mock function from the route controller
        mock_func = project_routes_with_custom_permission.custom_permission_func
        # Reset mock to ensure clean state for this test
        mock_func.reset_mock()

        # Include the router in the app
        client.app.include_router(project_routes_with_custom_permission.router)

        # Make a POST request
        data = {"name": "Test Project", "account_id": account.uuid}
        response = client.post(
            f"{project_routes_with_custom_permission.prefix}/",
            json=data,
            headers=auth_headers_with_permissions,
        )

        # Verify the custom permission function was called
        mock_func.assert_called_once()

        # Verify the function was called with correct arguments
        call_args = mock_func.call_args
        assert len(call_args[0]) == 2  # request and resource_data
        assert isinstance(call_args[0][0], Request)  # First argument should be Request
        assert isinstance(call_args[0][1], dict)  # Second argument should be dict

        # Verify the request was successful
        assert response.status_code == 201

    async def test_custom_permission_function_is_called_on_list(
        self,
        client,
        auth_headers_with_permissions,
        project_routes_with_custom_permission,
    ):
        """Test that custom permission function is called on GET list requests."""
        # Get the mock function from the route controller
        mock_func = project_routes_with_custom_permission.custom_permission_func
        # Reset mock to ensure clean state for this test
        mock_func.reset_mock()

        # Include the router in the app
        client.app.include_router(project_routes_with_custom_permission.router)

        # Make a GET request to list
        response = client.get(
            f"{project_routes_with_custom_permission.prefix}/",
            headers=auth_headers_with_permissions,
        )

        # Verify the custom permission function was called
        mock_func.assert_called_once()

        # Verify the request was successful
        assert response.status_code == 200

    async def test_custom_permission_function_is_called_on_update(
        self,
        client,
        auth_headers_with_permissions,
        project_routes_with_custom_permission,
        project,
    ):
        """Test that custom permission function is called on PUT requests."""
        # Get the mock function from the route controller
        mock_func = project_routes_with_custom_permission.custom_permission_func
        # Reset mock to ensure clean state for this test
        mock_func.reset_mock()

        # Include the router in the app
        client.app.include_router(project_routes_with_custom_permission.router)

        # Make a PUT request
        data = {"name": "Updated Project"}
        response = client.put(
            f"{project_routes_with_custom_permission.prefix}/{project.uuid}",
            json=data,
            headers=auth_headers_with_permissions,
        )

        # Verify the custom permission function was called
        mock_func.assert_called_once()

        # Verify the function was called with correct arguments
        call_args = mock_func.call_args
        assert call_args[0][1]["resource_id"] == project.uuid

        # Verify the request was successful
        assert response.status_code == 200

    async def test_custom_permission_function_is_called_on_delete(
        self,
        client,
        auth_headers_with_permissions,
        project_routes_with_custom_permission,
        project,
    ):
        """Test that custom permission function is called on DELETE requests."""
        # Get the mock function from the route controller
        mock_func = project_routes_with_custom_permission.custom_permission_func
        # Reset mock to ensure clean state for this test
        mock_func.reset_mock()

        # Include the router in the app
        client.app.include_router(project_routes_with_custom_permission.router)

        # Make a DELETE request
        response = client.delete(
            f"{project_routes_with_custom_permission.prefix}/{project.uuid}",
            headers=auth_headers_with_permissions,
        )

        # Verify the custom permission function was called
        mock_func.assert_called_once()

        # Verify the function was called with correct arguments
        call_args = mock_func.call_args
        assert call_args[0][1]["resource_id"] == project.uuid

        # Verify the request was successful
        assert response.status_code == 200

    async def test_custom_permission_function_denies_access_when_returns_false(
        self,
        client,
        auth_headers_with_permissions,
        project_routes_with_failing_custom_permission,
        project,
    ):
        """Test that custom permission function denies access when it returns False."""
        # Get the mock function from the route controller
        mock_func = project_routes_with_failing_custom_permission.custom_permission_func
        # Reset mock to ensure clean state for this test
        mock_func.reset_mock()

        # Include the router in the app
        client.app.include_router(project_routes_with_failing_custom_permission.router)

        # Make a GET request
        response = client.get(
            f"{project_routes_with_failing_custom_permission.prefix}/{project.uuid}",
            headers=auth_headers_with_permissions,
        )

        # Verify the custom permission function was called
        mock_func.assert_called_once()

        # Verify the request was denied with custom error message
        assert response.status_code == 403
        result = response.json()
        assert result["status"]["code"] == 403
        assert result["errors"][0]["message"] == "Custom permission denied"

    async def test_standard_permission_still_required_with_custom_permission(
        self,
        client,
        auth_headers_without_permissions,
        project_routes_with_custom_permission,
        project,
    ):
        """Test that standard permission is still required even with custom permission function."""
        # Get the mock function from the route controller
        mock_func = project_routes_with_custom_permission.custom_permission_func
        # Reset mock to ensure clean state for this test
        mock_func.reset_mock()

        # Include the router in the app
        client.app.include_router(project_routes_with_custom_permission.router)

        # Make a GET request without standard permissions
        response = client.get(
            f"{project_routes_with_custom_permission.prefix}/{project.uuid}",
            headers=auth_headers_without_permissions,
        )

        # Verify the request was denied due to missing standard permission
        assert response.status_code == 403
        result = response.json()
        assert result["status"]["code"] == 403
        assert "project:read" in result["errors"][0]["message"]

        # Verify the custom permission function was NOT called
        # because standard permission check failed first
        mock_func.assert_not_called()

    async def test_custom_permission_function_receives_correct_resource_data(
        self,
        client,
        auth_headers_with_permissions,
        project_routes_with_custom_permission,
        project,
    ):
        """Test that custom permission function receives correct resource data."""
        # Get the mock function from the route controller
        mock_func = project_routes_with_custom_permission.custom_permission_func
        # Reset mock to ensure clean state for this test
        mock_func.reset_mock()

        # Include the router in the app
        client.app.include_router(project_routes_with_custom_permission.router)

        # Make a GET request
        client.get(
            f"{project_routes_with_custom_permission.prefix}/{project.uuid}",
            headers=auth_headers_with_permissions,
        )

        # Verify the custom permission function was called
        mock_func.assert_called_once()

        # Verify the function was called with correct resource data
        call_args = mock_func.call_args
        resource_data = call_args[0][1]

        # Should contain resource_id for GET requests
        assert "resource_id" in resource_data
        assert resource_data["resource_id"] == project.uuid

        # Should not contain request or db parameters
        assert "request" not in resource_data
        assert "db" not in resource_data

    async def test_custom_permission_function_receives_data_for_create_requests(
        self,
        client,
        auth_headers_with_permissions,
        project_routes_with_custom_permission,
        account,
    ):
        """Test that custom permission function receives data for POST requests."""
        # Get the mock function from the route controller
        mock_func = project_routes_with_custom_permission.custom_permission_func
        # Reset mock to ensure clean state for this test
        mock_func.reset_mock()

        # Include the router in the app
        client.app.include_router(project_routes_with_custom_permission.router)

        # Make a POST request
        data = {"name": "Test Project", "account_id": account.uuid}
        client.post(
            f"{project_routes_with_custom_permission.prefix}/",
            json=data,
            headers=auth_headers_with_permissions,
        )

        # Verify the custom permission function was called
        mock_func.assert_called_once()

        # Verify the function was called with correct resource data
        call_args = mock_func.call_args
        resource_data = call_args[0][1]

        # Should contain the data for POST requests
        assert "data" in resource_data
        # The data is a Pydantic model, so we need to compare the dict representation
        data_dict = resource_data["data"]
        if hasattr(data_dict, "model_dump"):
            data_dict = data_dict.model_dump()
        # Only compare the fields that were in the original request
        assert data_dict["name"] == data["name"]
        assert data_dict["account_id"] == data["account_id"]

    async def test_no_custom_permission_function_works_normally(
        self,
        client,
        auth_headers_with_permissions,
        project_routes_without_custom_permission,
        project,
    ):
        """Test that routes work normally without custom permission function."""
        # Include the router in the app
        client.app.include_router(project_routes_without_custom_permission.router)

        # Make a GET request
        response = client.get(
            f"/test-projects-no-custom/{project.uuid}",
            headers=auth_headers_with_permissions,
        )

        # Verify the request was successful
        assert response.status_code == 200

    async def test_custom_permission_function_can_access_request_claims(
        self,
        client,
        auth_headers_with_permissions,
        project_routes_with_custom_permission,
        project,
    ):
        """Test that custom permission function can access request claims."""

        # Create a custom permission function that checks claims
        def custom_permission_with_claims_check(
            request: Request, _resource_data: Dict[str, Any]
        ) -> bool:
            claims = request.state.claims
            return claims.get("account_id") is not None

        # Create routes with this custom function
        custom_routes = RouteController(
            prefix="/test-projects-claims",
            tags=["Test Projects Claims"],
            controller=Project,
            get_db=get_db_engine,
            schema_response=ProjectResponse,
            schema_create=ProjectCreate,
            schema_update=ProjectUpdate,
            allowed_query_fields=["account_id", "name"],
            allowed_order_fields=["created_at", "name"],
            custom_permission_func=custom_permission_with_claims_check,
            custom_permission_error_message="Claims check failed",
        )

        # Include the router in the app
        client.app.include_router(custom_routes.router)

        # Make a GET request
        response = client.get(
            f"/test-projects-claims/{project.uuid}",
            headers=auth_headers_with_permissions,
        )

        # Verify the request was successful (claims check passed)
        assert response.status_code == 200

    async def test_custom_permission_function_with_invalid_claims_fails(
        self, client, project_routes_with_custom_permission, project
    ):
        """Test that custom permission function fails with invalid claims."""
        # Create headers without account_id in claims
        token = create_access_token(
            test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
            data={
                "sub": "test_user",
                "tenant_id": settings.AUTH_CLIENT_ID,
                "iss": settings.AUTH_ISSUER,
                "roles": ["user"],
                "permissions": ["project:read"],
                # No account_id in claims
            },
            expires_delta=timedelta(minutes=30),
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Create a custom permission function that requires account_id
        def custom_permission_requires_account_id(
            request: Request, _resource_data: Dict[str, Any]
        ) -> bool:
            claims = request.state.claims
            return claims.get("account_id") is not None

        # Create routes with this custom function
        custom_routes = RouteController(
            prefix="/test-projects-no-account",
            tags=["Test Projects No Account"],
            controller=Project,
            get_db=get_db_engine,
            schema_response=ProjectResponse,
            schema_create=ProjectCreate,
            schema_update=ProjectUpdate,
            allowed_query_fields=["account_id", "name"],
            allowed_order_fields=["created_at", "name"],
            custom_permission_func=custom_permission_requires_account_id,
            custom_permission_error_message="Account ID required",
        )

        # Include the router in the app
        client.app.include_router(custom_routes.router)

        # Make a GET request
        response = client.get(
            f"/test-projects-no-account/{project.uuid}",
            headers=headers,
        )

        # Verify the request was denied due to custom permission check
        assert response.status_code == 403
        result = response.json()
        assert result["status"]["code"] == 403
        assert result["errors"][0]["message"] == "Account ID required"
