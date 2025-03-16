"""Controller module for crud operations."""

from datetime import UTC, datetime
from typing import List, Optional, Type

from odmantic import AIOEngine, Model
from pydantic import BaseModel

from fastapi_sdk.utils.schema import datetime_now_sec


class Controller:
    """Base controller class."""

    model: Type[Model]
    schema_create: Type[BaseModel]
    schema_update: Type[BaseModel]
    n_per_page: int = 10

    def __init__(self, db_engine: AIOEngine):
        """Initialize the controller."""
        self.db_engine = db_engine

    async def _create(self, **kwargs) -> BaseModel:
        """Create a new model."""
        data = self.schema_create(**kwargs)
        model = self.model(**data.model_dump())
        return await self.db_engine.save(model)

    async def _update(self, uuid: str, data: dict) -> BaseModel:
        """Update a model."""
        model = await self._get(uuid)
        data = self.schema_update(**data)
        if model:
            # Update the fields submitted
            for field in data.model_dump(exclude_unset=True):
                setattr(model, field, data.model_dump()[field])
            model.updated_at = datetime_now_sec()
            return await self.db_engine.save(model)
        return None

    async def _get(self, uuid: str) -> BaseModel:
        """Get a model."""
        return await self.db_engine.find_one(
            self.model, self.model.uuid == uuid, self.model.deleted == False
        )

    async def _delete(self, uuid: str) -> BaseModel:
        """Delete a model."""
        model = await self._get(uuid)
        if model:
            model.deleted = True
            return await self.db_engine.save(model)
        return None

    async def _list(
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
