download_historical_news:
	chmod +x download_historical_news.sh
	./download_historical_news.sh

dataset:
	uv run ./dataset.py \
	--input_news data/cryptopanic_news.csv \
	--dataset_name news-sentiment-dataset-live \
	--teacher_model claude-opus-4-1-20250805 \
	--samples 10
tricky-example:
	uv run ./dataset.py \
	--input_news "I think ETH price will crash by the end of August 2025" \
	--dataset_name news-sentiment-dataset-live \
	--teacher_model claude-opus-4-1-20250805