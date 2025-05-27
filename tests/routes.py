"""Routes for the test application.

This module defines the routes for the test application using the FastAPI SDK's
RouteController. Currently includes account management endpoints.
"""

from fastapi_sdk.controllers import RouteController
from tests.controllers import Account, Project, Task
from tests.db import get_db_engine
from tests.schemas import (
    AccountCreate,
    AccountResponse,
    AccountResponsePaginated,
    AccountUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectResponsePaginated,
    ProjectUpdate,
    TaskCreate,
    TaskResponse,
    TaskResponsePaginated,
    TaskUpdate,
)

account_routes = RouteController(
    prefix="/accounts",
    tags=["Accounts"],
    controller=Account,
    get_db=get_db_engine,
    schema_response=AccountResponse,
    schema_response_paginated=AccountResponsePaginated,
    schema_create=AccountCreate,
    schema_update=AccountUpdate,
    allowed_query_fields=["name"],
    allowed_order_fields=["created_at", "name"],
)

project_routes = RouteController(
    prefix="/projects",
    tags=["Projects"],
    controller=Project,
    get_db=get_db_engine,
    schema_response=ProjectResponse,
    schema_response_paginated=ProjectResponsePaginated,
    schema_create=ProjectCreate,
    schema_update=ProjectUpdate,
    allowed_query_fields=["account_id", "name", "created_at", "status"],
    allowed_order_fields=["created_at", "name"],
)

task_routes = RouteController(
    prefix="/tasks",
    tags=["Tasks"],
    controller=Task,
    get_db=get_db_engine,
    schema_response=TaskResponse,
    schema_response_paginated=TaskResponsePaginated,
    schema_create=TaskCreate,
    schema_update=TaskUpdate,
    allowed_query_fields=["account_id", "project_id", "status"],
    allowed_order_fields=["created_at", "due_date", "status", "project.name"],
    ignored_query_fields=["description", "name"],
)
