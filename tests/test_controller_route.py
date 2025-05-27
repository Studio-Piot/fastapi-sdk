"""Tests for the RouteController."""

from datetime import timedelta

import pytest
from motor.core import AgnosticDatabase

from fastapi_sdk.utils.test import create_access_token
from tests.config import settings
from tests.constants import ProjectStatusOptions
from tests.controllers import Account, Project, Task
from tests.routes import project_routes


async def fixtures(db_engine: AgnosticDatabase, account: Account):
    """Re-usable test fictures"""
    superuser_claims = {"roles": ["superuser"]}
    # Create two accounts without claims (top-level model)
    account_1 = account
    account_2 = await Account(db_engine).create(
        {"name": "Account 2"}, claims=superuser_claims
    )

    project_11 = await Project(db_engine).create(
        {"name": "Project 11", "account_id": account_1.uuid},
        claims=superuser_claims,
    )
    project_12 = await Project(db_engine).create(
        {"name": "Project 12", "account_id": account_1.uuid},
        claims=superuser_claims,
    )
    project_21 = await Project(db_engine).create(
        {"name": "Project 21", "account_id": account_2.uuid},
        claims=superuser_claims,
    )
    project_22 = await Project(db_engine).create(
        {"name": "Project 22", "account_id": account_2.uuid},
        claims=superuser_claims,
    )
    task_111 = await Task(db_engine).create(
        {
            "name": "Task 111",
            "project_id": project_11.uuid,
            "account_id": account_1.uuid,
        },
        claims=superuser_claims,
    )
    task_112 = await Task(db_engine).create(
        {
            "name": "Task 112",
            "project_id": project_11.uuid,
            "account_id": account_1.uuid,
        },
        claims=superuser_claims,
    )
    task_113 = await Task(db_engine).create(
        {
            "name": "Task 113",
            "project_id": project_11.uuid,
            "account_id": account_1.uuid,
        },
        claims=superuser_claims,
    )
    task_121 = await Task(db_engine).create(
        {
            "name": "Task 121",
            "project_id": project_12.uuid,
            "account_id": account_1.uuid,
        },
        claims=superuser_claims,
    )
    task_122 = await Task(db_engine).create(
        {
            "name": "Task 122",
            "project_id": project_12.uuid,
            "account_id": account_1.uuid,
        },
        claims=superuser_claims,
    )

    return (
        account_1,
        account_2,
        project_11,
        project_12,
        project_21,
        project_22,
        task_111,
        task_112,
        task_113,
        task_121,
        task_122,
    )


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
        assert response.status_code == 201
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
        assert response.json() == {"detail": "Resource soft deleted"}

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
        assert response.status_code == 201
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
        assert response.json() == {"detail": "Resource soft deleted"}

    async def test_list_deleted_projects(self, client, auth_headers, deleted_project):
        """Test listing deleted projects."""
        response = client.get("/projects/deleted/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(p["uuid"] == deleted_project.uuid for p in data["items"])

    async def test_list_allowed_query_fields(
        self, client, auth_headers, db_engine, account
    ):
        """Test listing allowed query fields."""
        (
            _account_1,
            _account_2,
            _project_11,
            _project_12,
            _project_21,
            _project_22,
            _task_111,
            _task_112,
            _task_113,
            _task_121,
            _task_122,
        ) = await fixtures(db_engine, account)
        response = client.get("/projects/?name=Project 11", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert any(a["name"] == "Project 11" for a in data["items"])

        response = client.get(
            f"/projects/?account_id={account.uuid}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert any(a["account_id"] == account.uuid for a in data["items"])

    async def test_query_parameter_handling(
        self, client, auth_headers, db_engine, account
    ):
        """Test query parameter handling."""
        # Create test data
        await Project(db_engine).create(
            {
                "name": "Test Project",
                "account_id": account.uuid,
                "status": ProjectStatusOptions.ACTIVE.value,
            },
            claims={"account_id": account.uuid},
        )
        await Project(db_engine).create(
            {
                "name": "Another Project",
                "account_id": account.uuid,
                "status": ProjectStatusOptions.INACTIVE.value,
            },
            claims={"account_id": account.uuid},
        )

        # Test range query
        response = client.get(
            "/projects/?created_at=2023-01-01..2023-12-31", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 0  # Just verify the request succeeds

        # Test list values
        response = client.get("/projects/?status=active,pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 0

        # Test contains match
        response = client.get("/projects/?name=*Test*", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 0

        # Test comparison operators
        # Greater than
        response = client.get(
            "/projects/?created_at=gt:2023-01-01", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 0

        # Less than
        response = client.get(
            "/projects/?created_at=lt:2023-12-31", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 0

        # Greater than or equal
        response = client.get(
            "/projects/?created_at=gte:2023-01-01", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 0

        # Less than or equal
        response = client.get(
            "/projects/?created_at=lte:2023-12-31", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 0

        # Test exact match
        response = client.get("/projects/?name=Test Project", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Project"

        # Test invalid comparison operator
        response = client.get(
            "/projects/?created_at=invalid:2023-01-01", headers=auth_headers
        )
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Invalid comparison operator: invalid. Allowed operators: gt, lt, gte, lte"
        )

        # Test combining multiple query parameters
        response = client.get(
            "/projects/?name=*Test*&status=active&created_at=gt:2023-01-01",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 0

        # Test querying non-allowed field
        response = client.get("/projects/?invalid_field=value", headers=auth_headers)
        assert response.status_code == 400
        assert "Invalid query field: invalid_field" in response.json()["detail"]

    async def test_list_allowed_order_fields(
        self, client, auth_headers, db_engine, account
    ):
        """Test listing allowed order fields."""
        (
            _account_1,
            _account_2,
            _project_11,
            _project_12,
            _project_21,
            _project_22,
            _task_111,
            _task_112,
            _task_113,
            _task_121,
            _task_122,
        ) = await fixtures(db_engine, account)
        response = client.get("/projects/?order_by=name", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "Project 11"
        assert data["items"][1]["name"] == "Project 12"

        # Reverse order
        response = client.get(
            "/projects/?order_by=name&order_direction=desc", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "Project 12"
        assert data["items"][1]["name"] == "Project 11"

    async def test_list_projects_with_custom_pipeline(
        self, client, auth_headers, db_engine, account
    ):
        """Test listing projects with custom pipeline that includes latest task."""
        # Create test data
        (
            _account_1,
            _account_2,
            project_11,
            project_12,
            _project_21,
            _project_22,
            task_111,
            task_112,
            task_113,
            task_121,
            task_122,
        ) = await fixtures(db_engine, account)

        # Test the list endpoint
        response = client.get("/projects/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Find project 11 in the response
        project_11_data = next(p for p in data["items"] if p["uuid"] == project_11.uuid)
        print(project_11_data)
        assert "latest_task" in project_11_data
        assert (
            project_11_data["latest_task"]["uuid"] == task_113.uuid
        )  # Last task by name

        # Find project 12 in the response
        project_12_data = next(p for p in data["items"] if p["uuid"] == project_12.uuid)
        assert "latest_task" in project_12_data
        assert (
            project_12_data["latest_task"]["uuid"] == task_122.uuid
        )  # Last task by name


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
        assert response.status_code == 201
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

    async def test_get_with_relations(
        self, client, auth_headers, account, project, task
    ):
        """Test getting a resource with included relations."""
        # Test getting an account with projects included
        response = client.get(
            f"/accounts/{account.uuid}?include=projects", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == account.uuid
        assert "projects" in data
        assert len(data["projects"]) >= 1
        assert any(p["uuid"] == project.uuid for p in data["projects"])

        # Test getting a project with tasks and account included
        response = client.get(
            f"/projects/{project.uuid}?include=tasks&include=account",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == project.uuid
        assert "tasks" in data
        assert len(data["tasks"]) >= 1
        assert any(t["uuid"] == task.uuid for t in data["tasks"])
        assert "account" in data
        assert data["account"]["uuid"] == account.uuid

        # Test with non-existent relation
        response = client.get(
            f"/accounts/{account.uuid}?include=non_existent", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == account.uuid
        assert "non_existent" not in data

    async def test_list_tasks(self, client, auth_headers, task):
        """Test listing tasks."""
        response = client.get("/tasks/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(t["uuid"] == task.uuid for t in data["items"])

    async def test_list_tasks_with_n_per_page(
        self, client, auth_headers, db_engine, account
    ):
        """Test listing tasks with n_per_page parameter."""
        # Create multiple tasks for testing pagination
        project = await Project(db_engine).create(
            {"name": "Test Project", "account_id": account.uuid},
            claims={"account_id": account.uuid},
        )

        # Create 30 tasks
        tasks = []
        for i in range(30):
            task = await Task(db_engine).create(
                {
                    "name": f"Task {i}",
                    "description": f"Description {i}",
                    "project_id": project.uuid,
                    "account_id": account.uuid,
                },
                claims={"account_id": account.uuid},
            )
            tasks.append(task)

        # Test default n_per_page (25)
        response = client.get("/tasks/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 25  # Default page size
        assert data["total"] == 30
        assert data["page"] == 0
        assert data["pages"] == 2  # 30 items / 25 per page = 2 pages

        # Test custom n_per_page (10)
        response = client.get("/tasks/?n_per_page=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 30
        assert data["page"] == 0
        assert data["pages"] == 3  # 30 items / 10 per page = 3 pages

        # Test n_per_page exceeding max limit (300)
        response = client.get("/tasks/?n_per_page=300", headers=auth_headers)
        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "less_than_equal"
        assert response.json()["detail"][0]["loc"] == ["query", "n_per_page"]
        assert (
            response.json()["detail"][0]["msg"]
            == "Input should be less than or equal to 250"
        )
        assert response.json()["detail"][0]["input"] == "300"
        assert response.json()["detail"][0]["ctx"]["le"] == 250

        # Test pagination with custom n_per_page
        response = client.get("/tasks/?n_per_page=10&page=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 30
        assert data["page"] == 1
        assert data["pages"] == 3

        # Test last page with custom n_per_page
        response = client.get("/tasks/?n_per_page=10&page=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 30
        assert data["page"] == 2
        assert data["pages"] == 3

    async def test_list_with_relations(
        self, client, auth_headers, account, project, task
    ):
        """Test listing resources with included relations."""
        # Test listing accounts with projects included
        response = client.get("/accounts/?include=projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        account_data = next(a for a in data["items"] if a["uuid"] == account.uuid)
        assert "projects" in account_data
        assert len(account_data["projects"]) >= 1
        assert any(p["uuid"] == project.uuid for p in account_data["projects"])

        # Test listing projects with tasks included
        response = client.get(
            "/projects/?include=tasks&include=account", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        project_data = next(p for p in data["items"] if p["uuid"] == project.uuid)
        assert "tasks" in project_data
        assert len(project_data["tasks"]) >= 1
        assert any(t["uuid"] == task.uuid for t in project_data["tasks"])
        assert "account" in project_data
        assert project_data["account"]["uuid"] == account.uuid

        # Test listing tasks with multiple relations included
        response = client.get("/tasks/?include=project", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        task_data = next(t for t in data["items"] if t["uuid"] == task.uuid)
        assert "project" in task_data
        assert task_data["project"]["uuid"] == project.uuid

        # Test with non-existent relation
        response = client.get("/accounts/?include=non_existent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        account_data = next(a for a in data["items"] if a["uuid"] == account.uuid)
        assert "non_existent" not in account_data

    async def test_update_task(self, client, auth_headers, task):
        """Test updating a task."""
        response = client.put(
            f"/tasks/{task.uuid}",
            headers=auth_headers,
            json={"description": "Updated description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["due_date"] == task.due_date  # Unchanged

    async def test_delete_task(self, client, auth_headers, task):
        """Test deleting a task."""
        response = client.delete(f"/tasks/{task.uuid}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == {"detail": "Resource soft deleted"}

    async def test_list_deleted_tasks(self, client, auth_headers, deleted_task):
        """Test listing deleted tasks."""
        response = client.get("/tasks/deleted/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(t["uuid"] == deleted_task.uuid for t in data["items"])

    async def test_task_with_assignees(self, client, auth_headers, project, account):
        """Test creating and updating tasks with assignees through API routes."""
        # Create a task with assignees
        task_data = {
            "name": "Test Task",
            "description": "A test task with assignees",
            "project_id": project.uuid,
            "account_id": account.uuid,
            "assignees": [
                {
                    "uuid": "asn_123",
                    "name": "John Doe",
                    "email": "john@example.com",
                },
                {
                    "uuid": "asn_456",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                },
            ],
        }

        # Create the task
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json=task_data,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Task"
        assert len(data["assignees"]) == 2
        assert data["assignees"][0]["name"] == "John Doe"
        assert data["assignees"][0]["email"] == "john@example.com"
        assert data["assignees"][1]["name"] == "Jane Smith"
        assert data["assignees"][1]["email"] == "jane@example.com"

        # Update the task with new assignees
        updated_task_data = {
            "name": "Updated Task",
            "assignees": [
                {
                    "uuid": "asn_789",
                    "name": "Bob Wilson",
                    "email": "bob@example.com",
                },
            ],
        }

        response = client.put(
            f"/tasks/{data['uuid']}",
            headers=auth_headers,
            json=updated_task_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Task"
        assert len(data["assignees"]) == 1
        assert data["assignees"][0]["name"] == "Bob Wilson"
        assert data["assignees"][0]["email"] == "bob@example.com"

        # Test updating with empty assignees list
        empty_assignees_data = {
            "assignees": [],
        }

        response = client.put(
            f"/tasks/{data['uuid']}",
            headers=auth_headers,
            json=empty_assignees_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["assignees"]) == 0

    async def test_order_tasks_by_project_name(
        self, db_engine, client, auth_headers, account
    ):
        """Test ordering tasks by project name."""

        project_a = await Project(db_engine).create(
            {"name": "Test Project A", "account_id": account.uuid},
            claims={"account_id": account.uuid},
        )
        project_b = await Project(db_engine).create(
            {"name": "Test Project B", "account_id": account.uuid},
            claims={"account_id": account.uuid},
        )

        # Create 5 tasks for project a
        tasks = []
        for i in range(5):
            task = await Task(db_engine).create(
                {
                    "name": f"Task {i}",
                    "description": f"Description {i}",
                    "project_id": project_a.uuid,
                    "account_id": account.uuid,
                },
                claims={"account_id": account.uuid},
            )
            tasks.append(task)

        # Create 5 tasks for project b
        for i in range(5):
            task = await Task(db_engine).create(
                {
                    "name": f"Task {i}",
                    "description": f"Description {i}",
                    "project_id": project_b.uuid,
                    "account_id": account.uuid,
                },
                claims={"account_id": account.uuid},
            )
            tasks.append(task)

        response = client.get(
            "/tasks/?order_by=project.name&include=project", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["items"] == sorted(
            data["items"], key=lambda x: x["project"]["name"]
        )


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
        assert response.status_code == 201
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
                "tenant_id": settings.AUTH_CLIENT_ID,
                "iss": settings.AUTH_ISSUER,
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
                "tenant_id": settings.AUTH_CLIENT_ID,
                "iss": settings.AUTH_ISSUER,
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
                "tenant_id": settings.AUTH_CLIENT_ID,
                "iss": settings.AUTH_ISSUER,
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
        assert response.status_code == 201

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
        assert create_response.status_code == 201

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

    async def test_list_with_ignored_query_fields(
        self, client, auth_headers, db_engine, account
    ):
        """Test listing with ignored query fields."""

        # Create test data
        project = await Project(db_engine).create(
            {"name": "Test Project", "account_id": account.uuid},
            claims={"account_id": account.uuid},
        )

        # Create a task
        task = await Task(db_engine).create(
            {
                "name": "Test Task",
                "description": "Test Description",
                "project_id": project.uuid,
                "account_id": account.uuid,
            },
            claims={"account_id": account.uuid},
        )

        # Test that ignored fields are not used in filtering
        response = client.get(
            "/tasks/?description=Test&name=Test",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1  # Should return all tasks, ignoring the filters

        # Test that allowed fields still work
        response = client.get(
            f"/tasks/?project_id={project.uuid}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["uuid"] == task.uuid

        # Test that non-allowed fields still raise an error
        response = client.get(
            "/tasks/?due_date=2024-01-01",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert (
            "Invalid query field: due_date. Allowed fields: ['account_id', 'project_id', 'status']"
            in response.json()["detail"]
        )
