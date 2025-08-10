from typing import Optional

import pandas as pd
from loguru import logger
from opik import Opik
from tqdm import tqdm

from news_sentiment.baml_client.types import SentimentScores
from news_sentiment.sentiment_extractor import SentimentExctractor


def load_news_from_csv(input_csv_file: str, samples: Optional[int]) -> list[str]:
    """
    Returns a list of sample news from the given `input_csv_file`

    Args:
        input_csv_file (str): The input csv file
        samples (Optional[int]): The number of sample news to load

    Returns:
        list[str]: List of sample news
    """
    df = pd.read_csv(input_csv_file)
    if samples:
        df = df.sample(samples)
    return df['title'].to_list()


def generate(
    input_news: str,
    dataset_name: str,
    teacher_model: str,
    samples: Optional[int] = None,
):
    """
    Creates a dataset for the `input_csv_file` using the given `teacher_model`

    Args:
        input_csv_file (str): The csv file used to create the dataset
        dataset_name (str): The name of the dataset
        samples (int): The number of samples
        teacher_model (str): The model we use to bootstrap the dataset
    """
    if input_news.endswith('.csv'):
        input_csv_file = input_news
        # Load the news from the given csv file
        logger.info(f'Loading news from {input_csv_file}...')
        news: list[str] = load_news_from_csv(
            input_csv_file=input_csv_file, samples=samples
        )
        logger.info(f'Loaded {samples} news')
    else:
        logger.info(f'loading sing news item: {input_news}')
        news = [input_news]
    # Load the sentiment extractor to score the news
    sentiment_extractor = SentimentExctractor(model=teacher_model)
    # Create a dataset
    client = Opik()
    dataset = client.get_or_create_dataset(name=dataset_name)
    for news_item in tqdm(news):
        output: SentimentScores = sentiment_extractor.extract_sentiment_scores(
            news_item
        )
        # Extract the score of the output as a list of dicts
        output_scores = [
            {
                'coin': score.coin,
                'score': score.score,
            }
            for score in output.scores
        ]
        # Create a new row in the dataset
        row = {
            'input': news_item,
            'expected_output': output_scores,
            'expected_reason': output.reason,
            'teacher_model': teacher_model,
        }
        dataset.insert([row])


if __name__ == '__main__':
    from fire import Fire

    Fire(generate)
