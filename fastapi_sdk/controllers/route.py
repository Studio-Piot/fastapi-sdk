"""Route Controller for FastAPI SDK.

This module provides a base class for generating authenticated CRUD routes
with database and user dependencies.
"""

from datetime import datetime
from typing import Any, Callable, List, Optional, Type, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from fastapi_sdk.controllers import ModelController
from fastapi_sdk.security.permissions import require_permission
from fastapi_sdk.utils.model import convert_model_name
from fastapi_sdk.utils.schema import BaseResponsePaginated


class RouteController:
    """Base class for generating authenticated CRUD routes."""

    @staticmethod
    def _parse_date_value(value: str) -> Union[datetime, str]:
        """Parse a string value as a date if it matches ISO format, otherwise return as string.

        Args:
            value: The string value to parse

        Returns:
            Parsed datetime object if it's a valid ISO date, otherwise the original string
        """
        try:
            # Check if it looks like an ISO date format
            if "T" in value or value.count("-") >= 2:
                # Parse the date
                parsed_date = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed_date
            return value
        except (ValueError, TypeError):
            # If parsing fails, return the original string
            return value

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
        allowed_query_fields: Optional[List[str]] = None,
        allowed_order_fields: Optional[List[str]] = None,
        ignored_query_fields: Optional[List[str]] = None,
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
            allowed_query_fields: Optional list of fields that can be used in query parameters
            allowed_order_fields: Optional list of fields that can be used for ordering
            ignored_query_fields: Optional list of fields that should be ignored in query parameters
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
        self.allowed_query_fields = allowed_query_fields or []
        self.allowed_order_fields = allowed_order_fields or []
        self.ignored_query_fields = ignored_query_fields or []

        # Get model name from controller and convert it
        self.model_name = convert_model_name(controller.model.__name__)

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

        @self.router.post("/", response_model=self.schema_response, status_code=201)
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
            include: List[str] = Query(default=None),
            db: Any = Depends(self.get_db),
        ):
            """Get a resource by ID (requires authentication).

            Args:
                request: The FastAPI request object
                resource_id: The ID of the resource to get
                include: Optional list of related objects to include in the response
                db: The database connection

            Example:
                # Get an account with its projects included
                GET /accounts/{account_id}?include=projects

                # Get a project with its tasks included
                GET /projects/{project_id}?include=tasks

                # Get an account with multiple relations included
                GET /accounts/{account_id}?include=projects&include=tasks
            """
            if include:
                instance = await self.controller(db).get(
                    uuid=resource_id,
                    include=include,
                    claims=request.state.claims,
                )
            else:
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
            page: int = Query(default=1, ge=1, description="Page number (1-based)"),
            order_by: str = Query(
                default=None,
                description="Field(s) to order by (comma-separated for multiple fields)",
            ),
            order_direction: str = Query(
                default="asc",
                pattern="^(asc|desc)(,(asc|desc))*$",
                description="Order direction(s) (comma-separated for multiple fields, applies to all fields if single value)",
            ),
            include: List[str] = Query(
                default=None, description="List of related objects to include"
            ),
            n_per_page: int = Query(
                default=None,
                ge=1,
                le=250,
                description="Number of items per page (max 250)",
            ),
            db: Any = Depends(self.get_db),
        ):
            """List all resources (requires authentication).

            Args:
                request: The FastAPI request object
                page: Page number (1-based)
                order_by: Field(s) to order by (comma-separated for multiple fields)
                order_direction: Order direction(s) (comma-separated for multiple fields, applies to all fields if single value)
                include: List of related objects to include
                n_per_page: Number of items per page (max 250)
                db: The database connection

            Example:
                # List accounts with pagination
                GET /accounts/?page=1

                # List accounts with single field ordering
                GET /accounts/?order_by=created_at&order_direction=desc

                # List accounts with multiple field ordering (same direction for all)
                GET /accounts/?order_by=created_at,name&order_direction=desc

                # List accounts with multiple field ordering (different directions)
                GET /accounts/?order_by=created_at,name&order_direction=desc,asc

                # List accounts with filtering
                GET /accounts/?name=Test Account&status=active

                # List accounts with relations included
                GET /accounts/?include=projects

                # List accounts with custom page size
                GET /accounts/?n_per_page=50

                # Combine multiple parameters
                GET /accounts/?page=1&order_by=created_at,name&order_direction=desc,asc&include=projects&name=Test Account&n_per_page=50
            """
            # Get all query parameters
            query_params = dict(request.query_params)

            # Parse order_by parameter if provided
            order_by_dict = None
            if order_by:
                # Split order_by fields
                order_fields = [field.strip() for field in order_by.split(",")]

                # Validate all order_by fields
                for field in order_fields:
                    if field not in self.allowed_order_fields:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid order_by field: {field}. Allowed fields: {self.allowed_order_fields}",
                        )

                # Parse order_direction
                order_directions = [dir.strip() for dir in order_direction.split(",")]

                # If only one direction is provided, apply it to all fields
                if len(order_directions) == 1:
                    direction = 1 if order_directions[0] == "asc" else -1
                    order_by_dict = {field: direction for field in order_fields}
                else:
                    # Validate that we have the same number of directions as fields
                    if len(order_directions) != len(order_fields):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Number of order directions ({len(order_directions)}) must match number of order fields ({len(order_fields)})",
                        )

                    # Create order_by_dict with individual directions for each field
                    order_by_dict = {}
                    for field, direction_str in zip(order_fields, order_directions):
                        if direction_str not in ["asc", "desc"]:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Invalid order direction: {direction_str}. Must be 'asc' or 'desc'",
                            )
                        direction = 1 if direction_str == "asc" else -1
                        order_by_dict[field] = direction

            # Convert query parameters to filter list
            query_list = []
            for field, value in query_params.items():
                # Skip special parameters that are handled separately
                if (
                    field
                    in [
                        "page",
                        "order_by",
                        "order_direction",
                        "include",
                        "n_per_page",
                    ]
                    or field in self.ignored_query_fields
                ):
                    continue

                # Validate query field
                if field not in self.allowed_query_fields:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid query field: {field}. Allowed fields: {self.allowed_query_fields}",
                    )

                # Handle different value types
                if isinstance(value, str):
                    # Handle range queries (e.g., created_at=2023-01-01..2023-12-31)
                    if ".." in value:
                        start, end = value.split("..")
                        # Try to parse dates if they match ISO format
                        start_parsed = self._parse_date_value(start)
                        end_parsed = self._parse_date_value(end)

                        if isinstance(start_parsed, datetime) and isinstance(
                            end_parsed, datetime
                        ):
                            # Both are dates, check if they include time component
                            has_time = "T" in start or "T" in end

                            # If no time component was provided, adjust to start/end of day
                            if not has_time:
                                start_parsed = start_parsed.replace(
                                    hour=0, minute=0, second=0, microsecond=0
                                )
                                end_parsed = end_parsed.replace(
                                    hour=23, minute=59, second=59, microsecond=999999
                                )

                            query_list.append(
                                {field: {"$gte": start_parsed, "$lte": end_parsed}}
                            )
                        else:
                            # If not dates, use the original string values
                            query_list.append({field: {"$gte": start, "$lte": end}})
                    # Handle list values (e.g., status=active,pending)
                    elif "," in value:
                        values = value.split(",")
                        query_list.append({field: {"$in": values}})
                    # Handle contains match (e.g., name=*John*)
                    elif value.startswith("*") and value.endswith("*"):
                        contains_value = value[1:-1]  # Remove * and *
                        query_list.append(
                            {
                                field: {
                                    "$regex": f".*{contains_value}.*",
                                    "$options": "i",
                                }
                            }
                        )
                    # Handle comparison operators (e.g., age=gt:18, price=lt:100, created_at=gt:2023-01-01)
                    elif ":" in value:
                        operator, val = value.split(":", 1)
                        if operator in ["gt", "lt", "gte", "lte"]:
                            # Try to parse as date first
                            parsed_val = self._parse_date_value(val)

                            if isinstance(parsed_val, datetime):
                                # Use the parsed datetime value
                                mongo_operator = f"${operator}"
                                query_list.append({field: {mongo_operator: parsed_val}})
                            else:
                                # Try to convert to numeric value
                                try:
                                    numeric_val = float(val)
                                    # If it's a whole number, convert to int
                                    if numeric_val.is_integer():
                                        numeric_val = int(numeric_val)
                                    mongo_operator = f"${operator}"
                                    query_list.append(
                                        {field: {mongo_operator: numeric_val}}
                                    )
                                except ValueError:
                                    # If conversion fails, use the string value directly
                                    mongo_operator = f"${operator}"
                                    query_list.append({field: {mongo_operator: val}})
                        else:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Invalid comparison operator: {operator}. Allowed operators: gt, lt, gte, lte",
                            )
                    # Handle exact match (default)
                    else:
                        # Try to parse as date for exact matches too
                        parsed_val = self._parse_date_value(value)
                        query_list.append({field: parsed_val})
                else:
                    # For non-string values, try to parse as date if it's a string
                    if isinstance(value, str):
                        parsed_val = self._parse_date_value(value)
                        query_list.append({field: parsed_val})
                    else:
                        query_list.append({field: value})

            instances = await self.controller(db).list(
                page=page,
                query=query_list,
                order_by=order_by_dict,
                claims=request.state.claims,
                include=include,
                n_per_page=n_per_page,
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
            return {"detail": "Resource soft deleted"}

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

    def _get_query_filters(self, request: Request) -> List[dict]:
        """Get the query filters from the request.

        Args:
            request: The request object

        Returns:
            A list of query filters
        """
        query_filters = []
        for field, value in request.query_params.items():
            # Skip pagination, ordering, and include parameters
            if (
                field
                in [
                    "page",
                    "order_by",
                    "order_direction",
                    "include",
                    "n_per_page",
                ]
                or field in self.ignored_query_fields
            ):
                continue

            # Check if the field is allowed
            if field not in self.allowed_query_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field {field} is not allowed in query parameters",
                )

            # Add the filter
            query_filters.append({field: value})

        return query_filters
