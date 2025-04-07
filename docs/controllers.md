# Controllers

# Model controller

The model controller enable handle data between python code and database. It also define ownership rules and relationships with other models.

```python
class Project(ModelController):
    """Project controller."""

    model = ProjectModel
    schema_create = ProjectCreate
    schema_update = ProjectUpdate
    schema_response = ProjectResponse
    cascade_delete = True  # Will delete related tasks
    ownership_rule = OwnershipRule(
        claim_field="account_id",
        model_field="account_id",
        allow_public=False,
    )

    relationships = {
        "account": {
            "type": "many_to_one",
            "controller": "Account",
            "foreign_key": "account_id",
        },
        "tasks": {
            "type": "one_to_many",
            "controller": "Task",
            "foreign_key": "project_id",
        },
    }
```

The fully features model does the following:
- Reference the model in question
- Reference the create schema
- Reference the update schema
- Reference the single response schema
- Set the delete rule, cascade will auto-delete child items
- Ownership rule:
  - the claim field in the access token that needs to match
  - the model field to match against
  - if it has public access
- Relationship:
  - Auto-fetch parent items and add it to the response with many_to_one
  - Auto-fetch child items and add it to the response with one_to_many


# Route controller

Define a route using the model controller and schemas:

```python
account_routes = RouteController(
    prefix="/accounts",
    tags=["Accounts"],
    controller=Account,
    get_db=get_db_engine,
    schema_response=AccountResponse,
    schema_response_paginated=AccountResponsePaginated,
    schema_create=AccountCreate,
    schema_update=AccountUpdate,
)
```

- prefix is the base url for the route
- tags is for Open API docs
- controller reference to the model controller in question
- get_db is the async function that yield a database client
- schema_response defines the single API reponse
- schema_response_paginated defines the multiple API response
- schema_create defines to the data to be received on a POST request (create)
- schema_update defines to the data to be received on a PUT request (update)

# Adding models and routes to the app

Once you have defined your models and routes, you can now enable your app with those endpoints:

```python
from api.controllers import Account, Project, Task
from api.routes import account_routes, project_routes, task_routes


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    """
    # Register controllers
    ModelController.register_controller("Account", Account)
    ModelController.register_controller("Project", Project)
    ModelController.register_controller("Task", Task)

    app.include_router(account_routes.router)
    app.include_router(project_routes.router)
    app.include_router(task_routes.router)

    yield
```

We register the model in the model controller registry to enable importing models concurrently. If the account imports project and project imports account, it will create a conflicts so we use a registry for that. This features enabled loading models with other relationship models.

Finally, we add our route to the app lifespan.