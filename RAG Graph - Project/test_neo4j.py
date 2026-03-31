from neo4j import GraphDatabase

URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = "neo4j123"   # <-- replace with YOUR password

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

with driver.session() as session:
    result = session.run("RETURN 'Connection Successful!' AS message")
    record = result.single()
    print(record["message"])

driver.close()

