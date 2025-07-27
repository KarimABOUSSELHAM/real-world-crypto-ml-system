CREATE TABLE price_predictions (
    pair VARCHAR,
    ts_ms BIGINT,
    predicted_time_ms BIGINT,
    predicted_price FLOAT,
    -- useful for monitoring the model performance
    model_name VARCHAR,
    model_version INT,

    PRIMARY KEY (pair, ts_ms, model_name, model_version, predicted_time_ms)
);