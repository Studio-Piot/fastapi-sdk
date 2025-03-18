"""Tests for the RouteController."""

from datetime import timedelta

import pytest

from fastapi_sdk.utils.test import create_access_token
from tests.config import settings


@pytest.mark.asyncio
class TestAccountRoutes:
    """Test account routes."""

    async def test_create_account(self, client, auth_headers):
        """Test creating an account."""
        response = client.post(
            "/accounts/",
            headers=auth_headers,
            json={"name": "Test Account"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Account"
        assert "uuid" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_account(self, client, auth_headers, account):
        """Test getting an account by ID."""
        response = client.get(f"/accounts/{account.uuid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == account.uuid
        assert data["name"] == account.name

    async def test_list_accounts(self, client, auth_headers, account):
        """Test listing accounts."""
        response = client.get("/accounts/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(a["uuid"] == account.uuid for a in data["items"])

    async def test_update_account(self, client, auth_headers, account):
        """Test updating an account."""
        response = client.put(
            f"/accounts/{account.uuid}",
            headers=auth_headers,
            json={"name": "Updated Account"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Account"

    async def test_delete_account(self, client, auth_headers, account):
        """Test deleting an account."""
        response = client.delete(f"/accounts/{account.uuid}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Resource soft deleted"}

    # TODO: Fix this test
    # Only a superuser can list all top level resources, so we need to mock a superuser
    # async def test_list_deleted_accounts(self, client, auth_headers, deleted_account):
    #     """Test listing deleted accounts."""
    #     response = client.get("/accounts/deleted/", headers=auth_headers)
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert len(data["items"]) >= 1
    #     assert any(a["uuid"] == deleted_account.uuid for a in data["items"])


@pytest.mark.asyncio
class TestProjectRoutes:
    """Test project routes."""

    async def test_create_project(self, client, auth_headers, account):
        """Test creating a project."""
        response = client.post(
            "/projects/",
            headers=auth_headers,
            json={
                "name": "Test Project",
                "account_id": account.uuid,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["account_id"] == account.uuid

    async def test_get_project(self, client, auth_headers, project):
        """Test getting a project by ID."""
        response = client.get(f"/projects/{project.uuid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == project.uuid
        assert data["name"] == project.name

    async def test_list_projects(self, client, auth_headers, project):
        """Test listing projects."""
        response = client.get("/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(p["uuid"] == project.uuid for p in data["items"])

    async def test_update_project(self, client, auth_headers, project):
        """Test updating a project."""
        response = client.put(
            f"/projects/{project.uuid}",
            headers=auth_headers,
            json={"name": "Updated Project"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project"
        assert data["account_id"] == project.account_id  # Unchanged

    async def test_delete_project(self, client, auth_headers, project):
        """Test deleting a project."""
        response = client.delete(f"/projects/{project.uuid}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Resource soft deleted"}

    async def test_list_deleted_projects(self, client, auth_headers, deleted_project):
        """Test listing deleted projects."""
        response = client.get("/projects/deleted/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(p["uuid"] == deleted_project.uuid for p in data["items"])


@pytest.mark.asyncio
class TestTaskRoutes:
    """Test task routes."""

    async def test_create_task(self, client, auth_headers, project, account):
        """Test creating a task."""
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json={
                "name": "Test Task",
                "description": "Test Description",
                "project_id": project.uuid,
                "account_id": account.uuid,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Test Description"
        assert data["project_id"] == project.uuid
        assert data["account_id"] == account.uuid

    async def test_get_task(self, client, auth_headers, task):
        """Test getting a task by ID."""
        response = client.get(f"/tasks/{task.uuid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == task.uuid
        assert data["description"] == task.description

    async def test_list_tasks(self, client, auth_headers, task):
        """Test listing tasks."""
        response = client.get("/tasks/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(t["uuid"] == task.uuid for t in data["items"])

    async def test_update_task(self, client, auth_headers, task):
        """Test updating a task."""
        response = client.put(
            f"/tasks/{task.uuid}",
            headers=auth_headers,
            json={"description": "Updated description"},
        )
        print(response.json())
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["due_date"] == task.due_date  # Unchanged

    async def test_delete_task(self, client, auth_headers, task):
        """Test deleting a task."""
        response = client.delete(f"/tasks/{task.uuid}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Resource soft deleted"}

    async def test_list_deleted_tasks(self, client, auth_headers, deleted_task):
        """Test listing deleted tasks."""
        response = client.get("/tasks/deleted/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(t["uuid"] == deleted_task.uuid for t in data["items"])


@pytest.mark.asyncio
class TestAuthenticationAndErrors:
    """Test authentication and error handling."""

    async def test_missing_auth_header(self, client):
        """Test that requests without auth header fail."""
        response = client.get("/accounts/")
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing or invalid Authorization header"

    async def test_invalid_auth_token(self, client):
        """Test that requests with invalid auth token fail."""
        response = client.get(
            "/accounts/", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    async def test_resource_not_found(self, client, auth_headers):
        """Test 404 response for non-existent resources."""
        response = client.get(
            "/accounts/non_existent_uuid",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Resource not found"


@pytest.mark.asyncio
class TestOwnership:
    """Test ownership functionality at route level."""

    @pytest.fixture
    def account_claims(self, account):
        """Create test account claims."""
        return {"account_id": account.uuid}

    @pytest.fixture
    def different_account_claims(self):
        """Create claims for a different account."""
        return {"account_id": "acc_456"}

    @pytest.fixture
    def no_account_claims(self):
        """Create claims without account_id."""
        return {"user_id": "user_123"}

    async def test_create_with_ownership(self, client, auth_headers, account_claims):
        """Test creating a record with ownership."""
        data = {"name": "Test Project", "account_id": account_claims["account_id"]}
        response = client.post(
            "/projects/",
            json=data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Test Project"
        assert result["account_id"] == account_claims["account_id"]

    async def test_create_without_claims(
        self, client, account, auth_headers_no_account_id
    ):
        """Test creating a record without required claims."""
        data = {"name": "Test Project", "account_id": account.uuid}
        response = client.post(
            "/projects/",
            json=data,
            headers=auth_headers_no_account_id,
        )
        assert response.status_code == 403
        assert "Missing required claim: account_id" in response.json()["detail"]

    async def test_create_with_ownership_forbidden(self, client, auth_headers):
        """Test creating a record with incorrect ownership value is forbidden."""
        data = {
            "name": "Test Project",
            "account_id": "acc_999",  # Different from the claim value
        }
        response = client.post(
            "/projects/",
            json=data,
            headers=auth_headers,
        )
        assert response.status_code == 403
        assert "Invalid account_id" in response.json()["detail"]

    async def test_get_with_ownership(self, client, auth_headers, account_claims):
        """Test getting a record owned by the user."""
        # First create a project
        data = {"name": "Test Project", "account_id": account_claims["account_id"]}
        create_response = client.post(
            "/projects/",
            json=data,
            headers=auth_headers,
        )
        project_id = create_response.json()["uuid"]

        # Then get it
        response = client.get(
            f"/projects/{project_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert result["uuid"] == project_id
        assert result["account_id"] == account_claims["account_id"]

    async def test_get_without_ownership(
        self,
        client,
        auth_headers,
        different_auth_headers,
        account_claims,
    ):
        """Test getting a record not owned by the user."""
        # First create a project with one account
        data = {"name": "Test Project", "account_id": account_claims["account_id"]}
        create_response = client.post(
            "/projects/",
            json=data,
            headers=auth_headers,
        )
        project_id = create_response.json()["uuid"]

        # Try to get it with different account
        response = client.get(
            f"/projects/{project_id}",
            headers=different_auth_headers,
        )
        assert response.status_code == 404

    async def test_list_with_ownership(
        self,
        client,
        auth_headers,
        different_auth_headers,
        account_claims,
        different_account_claims,
    ):
        """Test listing records with ownership filter."""
        # Create projects for different accounts
        data = {"name": "Test Project 1", "account_id": account_claims["account_id"]}
        client.post(
            "/projects/",
            json=data,
            headers=auth_headers,
        )

        data = {
            "name": "Test Project 2",
            "account_id": different_account_claims["account_id"],
        }
        client.post(
            "/projects/",
            json=data,
            headers=different_auth_headers,
        )

        # List projects for first account
        response = client.get(
            "/projects/",
            headers=auth_headers,
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result["items"]) == 1
        assert result["items"][0]["account_id"] == account_claims["account_id"]

    async def test_update_with_ownership(
        self,
        client,
        auth_headers,
        different_auth_headers,
        account_claims,
    ):
        """Test updating records with ownership."""
        # First create a project
        data = {"name": "Test Project", "account_id": account_claims["account_id"]}
        create_response = client.post(
            "/projects/",
            json=data,
            headers=auth_headers,
        )
        project_id = create_response.json()["uuid"]

        # Update with correct ownership
        response = client.put(
            f"/projects/{project_id}",
            json={"name": "Updated Project"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Project"

        # Try to update with different account
        response = client.put(
            f"/projects/{project_id}",
            json={"name": "Hacked Project"},
            headers=different_auth_headers,
        )
        assert response.status_code == 404

    async def test_delete_with_ownership(
        self,
        client,
        auth_headers,
        different_auth_headers,
        account_claims,
    ):
        """Test deleting records with ownership."""
        # First create a project
        data = {"name": "Test Project", "account_id": account_claims["account_id"]}
        create_response = client.post(
            "/projects/",
            json=data,
            headers=auth_headers,
        )
        project_id = create_response.json()["uuid"]

        # Delete with correct ownership
        response = client.delete(
            f"/projects/{project_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Try to delete with different account
        response = client.delete(
            f"/projects/{project_id}",
            headers=different_auth_headers,
        )
        assert response.status_code == 404

    # TODO: Fix this test
    # Needs reviewing public routes
    # async def test_public_access(self, client, account_claims, no_account_claims):
    #     """Test access to public records."""
    #     # Create a project with account claims
    #     data = {"name": "Test Project", "account_id": account_claims["account_id"]}
    #     create_response = await client.post(
    #         "/projects/",
    #         json=data,
    #         headers={"X-User-Claims": str(account_claims)},
    #     )
    #     project_id = create_response.json()["uuid"]

    #     # Try to access with no claims
    #     response = await client.get(
    #         f"/projects/{project_id}",
    #         headers={"X-User-Claims": str(no_account_claims)},
    #     )
    #     assert response.status_code == 200
    #     result = response.json()
    #     assert result["uuid"] == project_id
    #     assert result["account_id"] == account_claims["account_id"]


@pytest.mark.asyncio
class TestPermissions:
    """Test permission functionality."""

    @pytest.fixture
    def auth_headers_read_permissions(self, account):
        """Create headers with JWT token."""
        token = create_access_token(
            test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
            data={
                "sub": "test_user",
                "account_id": account.uuid,
                "roles": ["user"],
                "permissions": ["project:read"],
            },
            expires_delta=timedelta(minutes=30),
        )
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def auth_headers_no_permissions(self, account):
        """Create headers with JWT token."""
        token = create_access_token(
            test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
            data={
                "sub": "test_user",
                "account_id": account.uuid,
                "roles": [],
                "permissions": [],
            },
            expires_delta=timedelta(minutes=30),
        )
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def auth_headers_superuser(self, account):
        """Create headers with JWT token."""
        token = create_access_token(
            test_private_key_path=settings.TEST_PRIVATE_KEY_PATH,
            data={
                "sub": "test_user",
                "account_id": account.uuid,
                "roles": ["superuser"],
                "permissions": [],
            },
            expires_delta=timedelta(minutes=30),
        )
        return {"Authorization": f"Bearer {token}"}

    async def test_create_with_permission(self, client, account, auth_headers):
        """Test creating a record with proper permission."""
        response = client.post(
            "/projects/",
            headers=auth_headers,
            json={"name": "Test Project", "account_id": account.uuid},
        )
        assert response.status_code == 200

    async def test_create_without_permission(
        self, client, account, auth_headers_no_permissions
    ):
        """Test creating a record without proper permission."""
        headers = auth_headers_no_permissions
        response = client.post(
            "/projects/",
            headers=headers,
            json={"name": "Test Project", "account_id": account.uuid},
        )
        assert response.status_code == 403
        assert "Permission denied: project:create required" in response.json()["detail"]

    async def test_read_with_permission(
        self, client, auth_headers_read_permissions, project
    ):
        """Test reading a record with proper permission."""
        response = client.get(
            f"/projects/{project.uuid}", headers=auth_headers_read_permissions
        )
        assert response.status_code == 200

    async def test_read_without_permission(
        self, client, auth_headers_no_permissions, project
    ):
        """Test reading a record without proper permission."""
        response = client.get(
            f"/projects/{project.uuid}", headers=auth_headers_no_permissions
        )
        assert response.status_code == 403
        assert "Permission denied: project:read required" in response.json()["detail"]

    async def test_update_with_permission(self, client, auth_headers, project):
        """Test updating a record with proper permission."""
        response = client.put(
            f"/projects/{project.uuid}",
            headers=auth_headers,
            json={"name": "Updated Project"},
        )
        assert response.status_code == 200

    async def test_update_without_permission(
        self, client, auth_headers_read_permissions, project
    ):
        """Test updating a record without proper permission."""
        response = client.put(
            f"/projects/{project.uuid}",
            headers=auth_headers_read_permissions,
            json={"name": "Updated Project"},
        )
        assert response.status_code == 403
        assert "Permission denied: project:update required" in response.json()["detail"]

    async def test_delete_with_permission(self, client, auth_headers, project):
        """Test deleting a record with proper permission."""
        response = client.delete(f"/projects/{project.uuid}", headers=auth_headers)
        assert response.status_code == 200

    async def test_delete_without_permission(
        self, client, auth_headers_read_permissions, project
    ):
        """Test deleting a record without proper permission."""
        response = client.delete(
            f"/projects/{project.uuid}", headers=auth_headers_read_permissions
        )
        assert response.status_code == 403
        assert "Permission denied: project:delete required" in response.json()["detail"]

    async def test_superuser_role_override(
        self, client, auth_headers_superuser, account, project
    ):
        """Test that admin role overrides permission checks."""

        headers = auth_headers_superuser

        # Try all operations
        create_response = client.post(
            "/projects/",
            headers=headers,
            json={"name": "Test Project", "account_id": account.uuid},
        )
        assert create_response.status_code == 200

        read_response = client.get(f"/projects/{project.uuid}", headers=headers)
        assert read_response.status_code == 200

        update_response = client.put(
            f"/projects/{project.uuid}",
            headers=headers,
            json={"name": "Updated Project"},
        )
        assert update_response.status_code == 200

        delete_response = client.delete(f"/projects/{project.uuid}", headers=headers)
        assert delete_response.status_code == 200
