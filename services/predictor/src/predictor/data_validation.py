import great_expectations as ge
import pandas as pd


def validate_data(
    ts_data: pd.DataFrame,
    max_percentage_rows_with_nulls: float,
) -> pd.DataFrame:
    """
    Runs a battery of validation checks on the time series data unless the percentage of rows with
    missing data is greater than max_percentage_rows_with_nulls.
    If any of the checks fails, an exception is raised, so the training process can be aborted.

    Args:
        ts_data (pd.DataFrame): input time series data to validate.
        max_percentage_rows_with_nulls (float): maximum allowed percentage of rows with null values.
    """
    # Check for missing values
    ts_data_without_nans = ts_data.dropna()
    percentage_rows_with_missing_data = 1 - len(ts_data_without_nans) / len(ts_data)
    if percentage_rows_with_missing_data > max_percentage_rows_with_nulls:
        raise Exception(
            f'Percentage of rows with missing data ({percentage_rows_with_missing_data:.2%}) '
            f'is greater than the allowed threshold ({max_percentage_rows_with_nulls:.2%})'
        )
    # We proceed with dataset without NaNs
    ts_data = ts_data_without_nans
    ge_df = ge.from_pandas(ts_data)
    validation_result = ge_df.expect_column_values_to_be_between(
        column='close',
        min_value=0,
    )
    if not validation_result.success:
        raise Exception("Column 'close' has values less then 0")

    # TODO: Add more validation checks
    # For example:
    # Check for null values
    # Check for duplicates
    # Check the data is sorted by timestamp
    return ts_data
