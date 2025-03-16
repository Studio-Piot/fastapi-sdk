"""FastAPI test application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    """

    # _app.include_router(
    #     project_routes,
    #     tags=["Customer API"],
    #     prefix="/customers",
    # )
    # app.include_router(
    #     product_routes,
    #     tags=["Product API"],
    #     prefix="/products",
    # )
    # app.include_router(
    #     machine_routes,
    #     tags=["Machine API"],
    #     prefix="/machines",
    # )
    # app.include_router(
    #     log_routes,
    #     tags=["Log API"],
    #     prefix="/logs",
    # )
    # app.include_router(
    #     survey_routes,
    #     tags=["Survey API"],
    #     prefix="/surveys",
    # )
    # app.include_router(
    #     stats_routes,
    #     tags=["Statistics API"],
    #     prefix="/stats",
    # )

    yield


app = FastAPI(
    title="FastAPI test appication",
    summary="",
    lifespan=lifespan,
)
