from news_sentiment.baml_client.sync_client import b
from news_sentiment.baml_client.types import SentimentScores


class SentimentExctractor:
    def __init__(self, model):
        self.model = model

    def extract_sentiment_scores(self, news: str) -> SentimentScores:
        return b.ExtractSentimentScores(news)


if __name__ == '__main__':
    sentiment_extractor = SentimentExctractor(model='ClaudeOpus4')
    print(
        sentiment_extractor.extract_sentiment_scores(
            'Goldman Sachs says it is going to buy soon 1 M BTC and sell 1 M ETH.'
        )
    )
