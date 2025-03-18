"""Tests for the RouteController."""

import pytest


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

    async def test_list_deleted_accounts(self, client, auth_headers, deleted_account):
        """Test listing deleted accounts."""
        response = client.get("/accounts/deleted/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(a["uuid"] == deleted_account.uuid for a in data["items"])


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
