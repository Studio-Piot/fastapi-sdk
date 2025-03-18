"""Controller module for crud operations."""

from datetime import UTC, datetime
from typing import List, Optional, Type

from odmantic import AIOEngine, Model
from pydantic import BaseModel

from fastapi_sdk.utils.schema import datetime_now_sec


class ModelController:
    """Base controller class."""

    model: Type[Model]
    schema_create: Type[BaseModel]
    schema_update: Type[BaseModel]
    n_per_page: int = 10
    relationships: dict = {}  # Define relationships between models
    cascade_delete: bool = False  # Whether to cascade delete related items
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

    async def create(self, data: dict) -> BaseModel:
        """Create a new model."""
        data = self.schema_create(**data)
        model = self.model(**data.model_dump())
        return await self.db_engine.save(model)

    async def update(self, uuid: str, data: dict) -> BaseModel:
        """Update a model."""
        model = await self.get(uuid)
        data = self.schema_update(**data)
        if model:
            # Update the fields submitted
            for field in data.model_dump(exclude_unset=True):
                setattr(model, field, data.model_dump()[field])
            model.updated_at = datetime_now_sec()
            return await self.db_engine.save(model)
        return None

    async def get(self, uuid: str) -> BaseModel:
        """Get a model."""
        return await self.db_engine.find_one(
            self.model, self.model.uuid == uuid, self.model.deleted == False
        )

    async def delete(self, uuid: str) -> BaseModel:
        """Delete a model."""
        model = await self.get(uuid)
        if model:
            model.deleted = True
            return await self.db_engine.save(model)
        return None

    async def list(
        self,
        page: int = 0,
        query: Optional[List[dict]] = None,
        order_by: Optional[dict] = None,
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
        # Example query: [{"due_date": {"$gte": start_date}}]
        _query = {"deleted": False}
        if query:
            for q in query:
                _query.update(q)

        # Sorting, default by created_at
        # Order by example: {"name": -1}, 1 ascending, -1 descending
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

        data = {
            "items": [self.model.model_validate_doc(item) for item in items],
            "total": total,
            "size": len(items),
            "page": page,
            "pages": pages,
        }

        return data

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
