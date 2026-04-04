from neo4j import GraphDatabase

class Neo4jExecutor:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))   #data connection

    def run_query(self, query):
        query = query.strip()

        # Add LIMIT 5 if not already present
        if "LIMIT" not in query.upper():
            query += "\nLIMIT 5"

        print("\nFinal Query Being Executed:\n", query)

        with self.driver.session() as session:
            result = session.run(query)                    #query execution

            records = []
            formatted_paths = set()

            for record in result:

                # 🔥 If query returns path
                if "p" in record:
                    path = record["p"]

                    nodes = list(path.nodes)
                    relationships = list(path.relationships)

                    for i in range(len(relationships)):
                        node1 = nodes[i]
                        rel = relationships[i]
                        node2 = nodes[i + 1]

                        label1 = list(node1.labels)[0]
                        label2 = list(node2.labels)[0]

                        value1 = (
                            node1.get("employee_id")
                            or node1.get("name")
                            or node1.get("status")
                        )

                        value2 = (
                            node2.get("employee_id")
                            or node2.get("name")
                            or node2.get("status")
                        )

                        formatted_paths.add(
                            f"{label1}({value1}) -[:{rel.type}]-> {label2}({value2})"
                        )

                else:
                    # Normal non-path query
                    records.append(record.data())

            # If we collected path data → return explainable output
            if formatted_paths:
                print("\n🔎 GRAPH PATH USED:\n")
                for fp in sorted(formatted_paths):
                    print(fp)
                return list(formatted_paths)

            # Otherwise return normal records
            return records

    def get_schema(self):
        with self.driver.session() as session:
            result = session.run("CALL db.schema.visualization()")
            return result.data()
