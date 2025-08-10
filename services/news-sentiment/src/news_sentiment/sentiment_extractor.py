from opik import track

from news_sentiment.baml_client.sync_client import b
from news_sentiment.baml_client.types import SentimentScores


class SentimentExctractor:
    def __init__(self, model):
        self.model = model

    @track
    def extract_sentiment_scores(self, news: str) -> SentimentScores:
        """
        Extract the sentiment scores for the given news

        Args:
            news (str): news given to score

        Returns:
            SentimentScores: Object instance which includes the scores
        """
        return b.ExtractSentimentScores(news)


if __name__ == '__main__':
    sentiment_extractor = SentimentExctractor(model='ClaudeOpus4')
    print(
        sentiment_extractor.extract_sentiment_scores(
            'Goldman Sachs says it is going to buy soon 1 M BTC and sell 1 M ETH.'
        )
    )
