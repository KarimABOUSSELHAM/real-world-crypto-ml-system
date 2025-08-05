from fastapi import FastAPI, HTTPException, Request
from lifespan import lifespan
from loguru import logger

app = FastAPI(lifespan=lifespan)


@app.get('/health')
async def read_root():
    return {'I am healthy!!!!'}


@app.get('/prediction')
async def get_prediction(request: Request, pair: str):
    logger.info('Connecting to the predictions database...')
    pool = request.app.state.db_pool
    logger.info(f'Requested prediction for {pair}')
    psql_view = request.app.state.config.psql_view_name
    query = f"""SELECT pair, predicted_price, ts_ms, predicted_ts_ms
    FROM public.{psql_view}
    WHERE pair = %(pair)s
    ORDER BY predicted_ts_ms DESC
    LIMIT 1
    """

    # query = text(query)
    # values={"pair": pair}
    logger.info(f'Running query: {query} with pair={pair}')
    # Query the latest price prediction from `pool` using the `query`
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, {'pair': pair})
            row = await cur.fetchone()
    if not row:
        logger.info(f'No prediction found for pair: {pair}')
        raise HTTPException(
            status_code=404, detail='No prediction found for this pair.'
        )
    columns = ['pair', 'predicted_price', 'ts_ms', 'predicted_ts_ms']
    result = dict(zip(columns, row, strict=False))
    return result
