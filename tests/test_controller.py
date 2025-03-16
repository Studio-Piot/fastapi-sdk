"""Test controller."""

import time
from datetime import UTC

import pytest
from motor.core import AgnosticDatabase

from tests.controllers import Account


@pytest.mark.asyncio
async def test_controller(db_engine: AgnosticDatabase):
    """Test controller."""

    # Create two accounts, one for crud test and one for listing
    account_1 = await Account(db_engine).create(name="Account 1")
    account_2 = await Account(db_engine).create(name="Account 2")

    assert account_1.uuid
    assert account_1.name == "Account 1"
    assert account_1.created_at
    assert account_1.updated_at

    # Get account
    account_1 = await Account(db_engine).get(uuid=account_1.uuid)
    assert account_1

    # Sleep for 1 seconds to test updated_at
    time.sleep(1)

    # Update account
    account_1 = await Account(db_engine).update(
        uuid=account_1.uuid, data={"name": "Account 1 Updated"}
    )

    assert account_1.name == "Account 1 Updated"
    assert account_1.updated_at > account_1.created_at.replace(tzinfo=UTC)

    # List accounts
    accounts = await Account(db_engine).list()
    assert len(accounts["items"]) == 2
    assert accounts["total"] == 2
    assert accounts["page"] == 0
    assert accounts["pages"] == 1

    # Delete account
    account_1 = await Account(db_engine).delete(uuid=account_1.uuid)
    assert account_1.deleted is True

    # Get deleted account
    deleted_account = await Account(db_engine).get(uuid=account_1.uuid)
    assert deleted_account is None

    # Update deleted account
    deleted_account = await Account(db_engine).update(
        uuid=account_1.uuid, data={"name": "Account 1 Updated"}
    )
    assert deleted_account is None

    # List accounts with one deleted
    accounts = await Account(db_engine).list()
    assert len(accounts["items"]) == 1
    assert accounts["items"][0].uuid == account_2.uuid
    assert accounts["total"] == 1
    assert accounts["page"] == 0
    assert accounts["pages"] == 1
