migrate:
	psql -h $(PSQL_HOST) -p $(PSQL_PORT) -d $(PSQL_DB) -U $(PSQL_USER) \
	-v view_name="$(PSQL_VIEW_NAME)" \
	-v table_name="$(PSQL_TABLE_NAME)" \
	-f latest_predictions.sql 