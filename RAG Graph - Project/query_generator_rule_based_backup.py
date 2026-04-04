def generate_cypher(question):

    question = question.lower()

    if "highest attrition" in question and "frequent" in question:
        return """
        MATCH (e:Employee)-[:TRAVELS]->(bt:BusinessTravel),
              (e)-[:WORKS_IN]->(d:Department),
              (e)-[:HAS_ATTRITION]->(a:Attrition)
        WHERE bt.type = 'Travel_Frequently'
          AND a.status = 'Yes'
        RETURN d.name AS department, count(e) AS attrition_count
        ORDER BY attrition_count DESC
        """

    return None
