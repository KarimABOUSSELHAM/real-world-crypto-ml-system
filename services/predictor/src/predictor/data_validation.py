import os
from pathlib import Path

import great_expectations as ge
import mlflow
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset
from mlflow.artifacts import download_artifacts


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
    # Check for duplicates
    ts_data.drop_duplicates(inplace=True)
    return ts_data


def generate_data_drift_report(
    ts_data: pd.DataFrame,
    experiment_name: str,
) -> str:
    """
    Generates a data drift report comparing the current dataset with the baseline dataset
    used by the model.

    Args:
        ts_data (pd.DataFrame): The current time series data to analyze.
        experiment_name (str): The name of the experiment to retrieve the baseline data.
    Returns:
        The path of the data drift report to log afterwards as mlflow artifact
    """
    # Use the mlflow sdk to get the experiment id for the last model in the model registry
    runs_df = mlflow.search_runs(
        experiment_names=[experiment_name],
        order_by=['start_time DESC'],
        max_results=1,
    )
    # breakpoint()
    latest_run = runs_df.iloc[0]
    run_id = latest_run.run_id
    # Download the ts_data used by the model from the model registry
    # artifact_list=list_artifacts(run_id=run_id)
    # breakpoint()
    last_registered_ts_data_root_folder = download_artifacts(run_id=run_id)
    last_registered_ts_data_path = (
        Path(last_registered_ts_data_root_folder) / 'datasets' / 'ts_data.csv'
    )
    # Now you have the current ts_data and the last model's ts_data
    # Compare the two datasets and generate a report using the library `evidenlty`
    last_registered_ts_data = pd.read_csv(last_registered_ts_data_path)
    report = Report([DataDriftPreset(method='psi')], include_tests='True')
    # breakpoint()
    my_eval = report.run(last_registered_ts_data, ts_data)
    report_name = 'data_drift_report.html'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(current_dir, report_name)
    # Save the report to an HTML file to mlflow artifacts
    my_eval.save_html(report_path)
    return report_path
