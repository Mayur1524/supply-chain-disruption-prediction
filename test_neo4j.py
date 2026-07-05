import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session(database="supplychain") as session:
    result = session.run("RETURN 'Neo4j connected!' AS msg")
    print(result.single()["msg"])

driver.close()
print("Connection test passed!")