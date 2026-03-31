from neo4j import GraphDatabase

URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = "neo4j123"   # replace with your password

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def create_graph(tx):
    tx.run("""
    
    MERGE (c1:Company {name: 'TechCorp', industry: 'Software'})
    MERGE (c2:Company {name: 'CloudSoft', industry: 'Cloud'})

    MERGE (p1:Person {name: 'Alice', role: 'Engineering Manager'})
    MERGE (p2:Person {name: 'Bob', role: 'Developer'})

    MERGE (proj1:Project {name: 'AI Platform', domain: 'Artificial Intelligence'})
    MERGE (proj2:Project {name: 'Cloud Migration', domain: 'Infrastructure'})

    MERGE (t1:Tool {name: 'Docker', category: 'Containerization'})
    MERGE (t2:Tool {name: 'TensorFlow', category: 'ML Framework'})

    MERGE (p1)-[:WORKS_AT]->(c1)
    MERGE (p2)-[:WORKS_AT]->(c1)

    MERGE (p1)-[:MANAGES]->(proj1)
    MERGE (p2)-[:MANAGES]->(proj2)

    MERGE (proj1)-[:DEPENDS_ON]->(t2)
    MERGE (proj2)-[:DEPENDS_ON]->(t1)

    MERGE (t1)-[:CREATED_BY]->(c2)

    """)

with driver.session() as session:
    session.execute_write(create_graph)

driver.close()

print("Graph Created Successfully!")

