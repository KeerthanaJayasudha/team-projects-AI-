def format_context(results):

    context_lines = []

    for row in results:

        for key, value in row.items():

            # Check if the value is a Neo4j path
            if hasattr(value, "nodes") and hasattr(value, "relationships"):

                nodes = list(value.nodes)
                rels = list(value.relationships)

                for i in range(len(rels)):

                    n1 = nodes[i]
                    r = rels[i]
                    n2 = nodes[i+1]

                    label1 = list(n1.labels)[0]
                    label2 = list(n2.labels)[0]

                    name1 = n1.get("employee_id") or n1.get("name") or n1.get("status")
                    name2 = n2.get("employee_id") or n2.get("name") or n2.get("status")

                    context_lines.append(
                        f"{label1}({name1}) -[{r.type}]-> {label2}({name2})"
                    )

    return "\n".join(context_lines)