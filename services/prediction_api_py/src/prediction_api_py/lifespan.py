from contextlib import asynccontextmanager

from config import config
from database import get_database
from fastapi import FastAPI
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Store the config in the app state
    app.state.config = config
    # Connect to the existing database
    app.state.db_pool = await get_database(
        psql_host=config.psql_host,
        psql_port=config.psql_port,
        psql_db=config.psql_db,
        psql_user=config.psql_user,
        psql_password=config.psql_password,
    )
    view_name = config.psql_view_name
    table_name = config.psql_table_name
    logger.info('Connected to database.')
    # Create or refresh the materialized view
    logger.info('Ensuring materialized view exists...')
    with open('../../drop_latest_predictions.sql', 'r') as f:
        drop_sql = f.read().replace(':view_name', view_name)
    with open('../../create_latest_predictions.sql', 'r') as f:
        create_sql = (
            f.read().replace(':view_name', view_name).replace(':table_name', table_name)
        )
    # Acquire a connection and execute the SQL commands
    async with app.state.db_pool.connection() as conn:
        await conn.execute(drop_sql)
        await conn.execute(create_sql)
    yield
    #  Close the database connection
    logger.info('Shutting down and closing DB connection...')
    await app.state.db_pool.close()
