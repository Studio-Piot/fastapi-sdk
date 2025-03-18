"""Route Controller for FastAPI SDK.

This module provides a base class for generating authenticated CRUD routes
with database and user dependencies.
"""

from typing import Any, Callable, List, Optional, Type

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from fastapi_sdk.controllers import ModelController
from fastapi_sdk.security.permissions import require_permission
from fastapi_sdk.utils.schema import BaseResponsePaginated


class RouteController:
    """Base class for generating authenticated CRUD routes."""

    def __init__(
        self,
        *,
        prefix: str,
        tags: List[str],
        controller: Type[ModelController],
        get_db: Callable,
        schema_response: Type[BaseModel],
        schema_response_paginated: Type[BaseResponsePaginated],
        schema_create: Optional[Type[BaseModel]] = None,
        schema_update: Optional[Type[BaseModel]] = None,
        include_routes: Optional[List[str]] = None,
    ):
        """Initialize the route controller.

        Args:
            prefix: The prefix for all routes (e.g., "/products")
            tags: List of tags for API documentation
            controller: The ModelController class to use
            get_db: Database dependency function
            schema_response: Pydantic model for response
            schema_response_paginated: Pydantic model for paginated response
            schema_create: Optional Pydantic model for creation
            schema_update: Optional Pydantic model for updates
            include_routes: Optional list of routes to include (defaults to all)
                          Valid options: ["create", "get", "list", "update", "delete", "list_deleted"]
        """
        self.prefix = prefix
        self.tags = tags
        self.controller = controller
        self.get_db = get_db
        self.schema_response = schema_response
        self.schema_response_paginated = schema_response_paginated
        self.schema_create = schema_create
        self.schema_update = schema_update
        self.include_routes = include_routes or [
            "create",
            "get",
            "list",
            "update",
            "delete",
            "list_deleted",
        ]

        # Get model name for permissions
        self.model_name = controller.model.__name__.lower().replace("model", "")

        self.router = APIRouter(prefix=prefix, tags=tags)
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up all the CRUD routes based on include_routes."""
        if "create" in self.include_routes and self.schema_create:
            self._add_create_route()

        if "get" in self.include_routes:
            self._add_get_route()

        if "list" in self.include_routes:
            self._add_list_route()

        if "update" in self.include_routes and self.schema_update:
            self._add_update_route()

        if "delete" in self.include_routes:
            self._add_delete_route()

        if "list_deleted" in self.include_routes:
            self._add_list_deleted_route()

    def _add_create_route(self) -> None:
        """Add create route."""

        @self.router.post("/", response_model=self.schema_response)
        @require_permission(f"{self.model_name}:create")
        async def create_route(
            request: Request,
            data: self.schema_create,  # type: ignore
            db: Any = Depends(self.get_db),
        ):
            """Create a new resource (requires authentication)."""
            instance = await self.controller(db).create(
                data.model_dump(),
                claims=request.state.claims,
            )
            return self.schema_response(**instance.model_dump())

    def _add_get_route(self) -> None:
        """Add get by ID route."""

        @self.router.get("/{resource_id}", response_model=self.schema_response)
        @require_permission(f"{self.model_name}:read")
        async def get_route(
            request: Request,
            resource_id: str,
            db: Any = Depends(self.get_db),
        ):
            """Get a resource by ID (requires authentication)."""
            instance = await self.controller(db).get(
                uuid=resource_id,
                claims=request.state.claims,
            )
            if not instance:
                raise HTTPException(status_code=404, detail="Resource not found")
            return self.schema_response(**instance.model_dump())

    def _add_list_route(self) -> None:
        """Add list route."""

        @self.router.get("/", response_model=self.schema_response_paginated)
        @require_permission(f"{self.model_name}:read")
        async def list_route(
            request: Request,
            db: Any = Depends(self.get_db),
        ):
            """List all resources (requires authentication)."""
            instances = await self.controller(db).list(
                claims=request.state.claims,
            )
            return instances

    def _add_update_route(self) -> None:
        """Add update route."""

        @self.router.put("/{resource_id}", response_model=self.schema_response)
        @require_permission(f"{self.model_name}:update")
        async def update_route(
            request: Request,
            resource_id: str,
            data: self.schema_update,  # type: ignore
            db: Any = Depends(self.get_db),
        ):
            """Update a resource (requires authentication)."""
            instance = await self.controller(db).update(
                uuid=resource_id,
                data=data.model_dump(exclude_unset=True),
                claims=request.state.claims,
            )
            if not instance:
                raise HTTPException(status_code=404, detail="Resource not found")
            return self.schema_response(**instance.model_dump())

    def _add_delete_route(self) -> None:
        """Add delete route."""

        @self.router.delete("/{resource_id}")
        @require_permission(f"{self.model_name}:delete")
        async def delete_route(
            request: Request,
            resource_id: str,
            db: Any = Depends(self.get_db),
        ):
            """Soft delete a resource (requires authentication)."""
            if not await self.controller(db).delete(
                uuid=resource_id,
                claims=request.state.claims,
            ):
                raise HTTPException(status_code=404, detail="Resource not found")
            return {"message": "Resource soft deleted"}

    def _add_list_deleted_route(self) -> None:
        """Add list deleted route."""

        @self.router.get("/deleted/", response_model=self.schema_response_paginated)
        @require_permission(f"{self.model_name}:read")
        async def list_deleted_route(
            request: Request,
            db: Any = Depends(self.get_db),
        ):
            """List all deleted resources (requires authentication)."""
            instances = await self.controller(db).list(
                query=[{"deleted": True}],
                claims=request.state.claims,
            )
            return instances
