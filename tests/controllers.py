"""Controllers for tests."""

from typing import List

from fastapi_sdk.controller import Controller
from tests.models import AccountModel
from tests.schemas import AccountCreate, AccountResponse, AccountUpdate


class Account(Controller):
    """Account controller."""

    model = AccountModel
    schema_create = AccountCreate
    schema_update = AccountUpdate
    schema_response = AccountResponse

    async def create(self, name: str) -> AccountResponse:
        """Create a account."""
        return await self._create(name=name)

    async def update(self, uuid: str, data: dict) -> AccountResponse:
        """Update a account."""
        return await self._update(uuid=uuid, data=data)

    async def get(self, uuid: str) -> AccountResponse:
        """Get a account."""
        return await self._get(uuid=uuid)

    async def delete(self, uuid: str) -> AccountResponse:
        """Delete a account."""
        return await self._delete(uuid=uuid)

    async def list(self) -> List[AccountResponse]:
        """List accounts."""
        return await self._list()
