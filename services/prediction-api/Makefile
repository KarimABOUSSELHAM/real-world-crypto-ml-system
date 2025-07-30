migrate:
	psql -h $(PSQL_HOST) -p $(PSQL_PORT) -d $(PSQL_DB) -U $(PSQL_USER) \
	-v view_name="$(PSQL_VIEW_NAME)" \
	-v table_name="$(PSQL_TABLE_NAME)" \
	-f latest_predictions.sql 
build:
	docker build -t prediction-api:dev .
run:
	docker run -it -p $(PREDICTION_API_PORT):$(PREDICTION_API_PORT) \
	-e PSQL_HOST=$(PSQL_HOST) \
	-e PSQL_PORT=$(PSQL_PORT) \
	-e PSQL_DB=$(PSQL_DB) \
	-e PSQL_USER=$(PSQL_USER) \
	-e PSQL_PASSWORD=$(PSQL_PASSWORD) \
	-e PSQL_VIEW_NAME=$(PSQL_VIEW_NAME) \
	-e PSQL_TABLE_NAME=$(PSQL_TABLE_NAME) \
	-e PREDICTION_API_PORT=$(PREDICTION_API_PORT) \
	-e RUST_LOG=$(RUST_LOG) \
	prediction-api:dev