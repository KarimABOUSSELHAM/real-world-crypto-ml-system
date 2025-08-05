from psycopg_pool import AsyncConnectionPool


async def get_database(
    psql_host: str,
    psql_port: int,
    psql_db: str,
    psql_user: str,
    psql_password: str,
) -> AsyncConnectionPool:
    dsn = f'postgresql://{psql_user}:{psql_password}@{psql_host}:{psql_port}/{psql_db}'
    db_pool = AsyncConnectionPool(dsn)
    return db_pool
