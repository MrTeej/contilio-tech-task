from api.connectors.db.db_connector import DatabaseConnector

print("Setting up Database")
db_connector = DatabaseConnector()
db_connector.create_db()
db_connector.close()
print("Finished setting up Database")
