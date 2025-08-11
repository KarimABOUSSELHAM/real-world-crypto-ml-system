from typing import Optional

from fire import Fire
from opik import Opik
from opik.evaluation import evaluate

from news_sentiment.metrics import SameScoreMetric
from news_sentiment.sentiment_extractor import SentimentExctractor


def evaluate_sentiment_extractor(
    dataset_name: str,
    model: str,
    dataset_item_id: Optional[str] = None,
):
    """
    Evaluate the sentiment extractor model on the given dataset

    Args:
        dataset_name (str): Name of the dataset
        model (str): The model name
    """
    #  Load the dataset form opik
    client = Opik()
    dataset = client.get_or_create_dataset(name=dataset_name)
    #  Load the sentiment extractor solution we want to evaluate*
    sentiment_extractor = SentimentExctractor(model=model)
    #  Define the evaluation metrics
    same_eth_score_metric = SameScoreMetric(name='same_eth_score_metric', coin='ETH')

    # Define the evaluation task
    def evaluation_task(x):
        return {
            'scores': sentiment_extractor.extract_sentiment_scores(x['input']).scores,
            'reason': sentiment_extractor.extract_sentiment_scores(x['input']).reason,
        }

    #  Launch the evaluation porcess
    evaluation = evaluate(
        dataset=dataset,
        task=evaluation_task,
        scoring_metrics=[same_eth_score_metric],
        experiment_config={'model': model},
        task_threads=1,
        dataset_item_ids=dataset_item_id if dataset_item_id else None,
    )
    # Print the evaluation results
    print(evaluation)


if __name__ == '__main__':
    Fire(evaluate_sentiment_extractor)
