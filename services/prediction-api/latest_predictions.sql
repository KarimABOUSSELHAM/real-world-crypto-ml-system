DROP materialized view if exists :view_name;
CREATE materialized view :view_name AS
WITH :view_name AS (
    SELECT
        pair,
        MAX(ts_ms) AS last_ts
    FROM :table_name
    GROUP BY 1
) 

SELECT
    p.pair,
    p.predicted_price,
    p.ts_ms,
    p.predicted_ts_ms
FROM
    public.predictions p
    INNER JOIN latest_predictions lp
        ON p.pair= lp.pair
        AND p.ts_ms=lp.last_ts
;