"""Controller module for crud operations."""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Type, Union

from fastapi import HTTPException
from odmantic import AIOEngine, Model
from pydantic import BaseModel

from fastapi_sdk.utils.schema import datetime_now_sec


class OwnershipRule:
    """Rule for filtering records based on user claims."""

    def __init__(
        self,
        *,
        claim_field: str,
        model_field: str,
        allow_public: bool = False,
    ):
        """Initialize the ownership rule.

        Args:
            claim_field: The field in the user claims to use (e.g., "account_id")
            model_field: The field in the model to match against (e.g., "account_id")
            allow_public: Whether to allow access to records without ownership
        """
        self.claim_field = claim_field
        self.model_field = model_field
        self.allow_public = allow_public


class ModelController:
    """Base controller class."""

    model: Type[Model]
    schema_create: Type[BaseModel]
    schema_update: Type[BaseModel]
    n_per_page: int = 10
    relationships: dict = {}  # Define relationships between models
    cascade_delete: bool = False  # Whether to cascade delete related items
    ownership_rule: Optional[OwnershipRule] = None  # Rule for filtering records
    _controller_registry: dict = {}  # Registry for controller classes

    def __init__(self, db_engine: AIOEngine):
        """Initialize the controller."""
        self.db_engine = db_engine

    @classmethod
    def register_controller(
        cls, name: str, controller_class: Type["ModelController"]
    ) -> None:
        """Register a controller class."""
        cls._controller_registry[name] = controller_class

    @classmethod
    def get_controller(cls, name: str) -> Type["ModelController"]:
        """Get a controller class by name."""
        return cls._controller_registry[name]

    def _get_ownership_filter(self, claims: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the ownership filter based on user claims.

        Args:
            claims: The user claims from the JWT token

        Returns:
            A filter dictionary or None if no ownership rule is set
        """
        if not self.ownership_rule:
            return None

        claim_value = claims.get(self.ownership_rule.claim_field)
        if not claim_value and not self.ownership_rule.allow_public:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required claim: {self.ownership_rule.claim_field}",
            )

        return {self.ownership_rule.model_field: claim_value} if claim_value else None

    async def create(
        self, data: dict, claims: Optional[Dict[str, Any]] = None
    ) -> BaseModel:
        """Create a new model."""
        data = self.schema_create(**data)
        data_dict = data.model_dump()

        # Verify ownership if rule exists
        if self.ownership_rule and claims:
            ownership_filter = self._get_ownership_filter(claims)
            if ownership_filter and self.ownership_rule.model_field != "uuid":
                # Check if the provided data matches the user's claim
                if (
                    data_dict.get(self.ownership_rule.model_field)
                    != ownership_filter[self.ownership_rule.model_field]
                ):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Invalid {self.ownership_rule.model_field}",
                    )

        model = self.model(**data_dict)
        return await self.db_engine.save(model)

    async def update(
        self, uuid: str, data: dict, claims: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseModel]:
        """Update a model."""
        model = await self.get(uuid, claims)
        if not model:
            return None

        data = self.schema_update(**data)
        # Update the fields submitted
        for field in data.model_dump(exclude_unset=True):
            setattr(model, field, data.model_dump()[field])
        model.updated_at = datetime_now_sec()
        return await self.db_engine.save(model)

    async def get(
        self, uuid: str, claims: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseModel]:
        """Get a model."""
        query = (self.model.uuid == uuid) & (self.model.deleted == False)

        # Apply ownership filter if rule exists
        if self.ownership_rule and claims:
            ownership_filter = self._get_ownership_filter(claims)
            if ownership_filter:
                query = (
                    (self.model.uuid == uuid)
                    & (self.model.deleted == False)
                    & (
                        getattr(self.model, self.ownership_rule.model_field)
                        == ownership_filter[self.ownership_rule.model_field]
                    )
                )

        return await self.db_engine.find_one(self.model, query)

    async def delete(
        self, uuid: str, claims: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseModel]:
        """Delete a model."""
        model = await self.get(uuid, claims)
        if model:
            model.deleted = True
            return await self.db_engine.save(model)
        return None

    async def list(
        self,
        page: int = 0,
        query: Optional[List[dict]] = None,
        order_by: Optional[dict] = None,
        claims: Optional[Dict[str, Any]] = None,
    ) -> List[BaseModel]:
        """List models."""
        # Get the collection
        collection_name = self.model.model_config[
            "collection"
        ] or self.model.__name__.lower().replace("model", "")
        _collection = self.db_engine.database[collection_name]

        # Create a pipeline for aggregation
        _pipeline = []

        # Filter out deleted models by default
        _query = {"deleted": False}
        if query:
            for q in query:
                _query.update(q)

        # Apply ownership filter if rule exists
        if self.ownership_rule and claims:
            ownership_filter = self._get_ownership_filter(claims)
            if ownership_filter:
                _query.update(ownership_filter)

        # Sorting, default by created_at
        _sort = order_by if order_by else {"created_at": -1}

        # Add the pipeline stages
        _pipeline.append({"$match": _query})
        _pipeline.append({"$sort": _sort})

        # Add pagination data
        _pipeline.append({"$skip": (page - 1) * self.n_per_page if page > 0 else 0})
        _pipeline.append({"$limit": self.n_per_page})

        # Execute the aggregation
        items = await _collection.aggregate(_pipeline).to_list(length=self.n_per_page)

        # Count the total number of items
        total = await _collection.count_documents(_query)

        pages = total // self.n_per_page
        if total % self.n_per_page > 0:
            pages += 1

        return {
            "items": [self.model.model_validate_doc(item) for item in items],
            "total": total,
            "page": page,
            "pages": pages,
            "size": len(items),
        }

    async def list_related(self, foreign_key: str, value: str) -> List[BaseModel]:
        """List related models by foreign key."""
        result = await self.list(query=[{foreign_key: value}])
        return result["items"]

    async def get_with_relations(
        self, uuid: str, include: Optional[List[str]] = None
    ) -> BaseModel:
        """Get a model with its relationships."""
        model = await self.get(uuid)
        if not model or not include:
            return model

        for relation in include:
            if relation not in self.relationships:
                continue

            rel_info = self.relationships[relation]
            rel_controller_name = rel_info["controller"]
            rel_type = rel_info["type"]
            foreign_key = rel_info.get("foreign_key")

            # Get the controller class from the registry
            rel_controller_class = self.get_controller(rel_controller_name)

            if rel_type == "one_to_many":
                # Fetch related items where foreign_key matches this model's uuid
                related_items = await rel_controller_class(self.db_engine).list_related(
                    foreign_key=foreign_key, value=model.uuid
                )
                setattr(model, relation, related_items)
            elif rel_type == "many_to_one":
                # Fetch single related item
                related_item = await rel_controller_class(self.db_engine).get(
                    uuid=getattr(model, foreign_key)
                )
                setattr(model, relation, related_item)

        return model

    async def delete_with_relations(self, uuid: str) -> BaseModel:
        """Delete a model and its related items if cascade_delete is True."""
        model = await self.get(uuid)
        if not model:
            return None

        if self.cascade_delete:
            for rel_info in self.relationships.values():
                if rel_info["type"] == "one_to_many":
                    rel_controller_name = rel_info["controller"]
                    foreign_key = rel_info.get("foreign_key")

                    # Get the controller class from the registry
                    rel_controller_class = self.get_controller(rel_controller_name)

                    # Find all related items
                    related_items = await rel_controller_class(
                        self.db_engine
                    ).list_related(foreign_key=foreign_key, value=uuid)
                    # Delete each related item
                    for item in related_items:
                        await rel_controller_class(
                            self.db_engine
                        ).delete_with_relations(item.uuid)

        return await self.delete(uuid)
