# Graph RAG Employee Knowledge Assistant

## Project Overview

This project implements a **Graph Retrieval-Augmented Generation (Graph RAG) system** that answers user questions using both:

* **Knowledge Graph reasoning**
* **Vector similarity search**

The system builds a **knowledge graph from an HR dataset**, stores entities and relationships in **Neo4j**, retrieves relevant subgraphs using **Cypher queries**, and combines them with **vector-based document retrieval** to generate explainable answers using an LLM.

Unlike traditional RAG systems that rely only on vector similarity, this project demonstrates **graph reasoning through relationship traversal (k-hop queries)**.

---

# System Architecture

User Question
↓
LLM generates **Cypher Query**
↓
Neo4j executes **Graph Traversal**
↓
Relevant **Subgraph Retrieved**
↓
Vector Search retrieves supporting documents
↓
Graph + Vector context combined
↓
LLM generates final **explainable answer**

---

# Technologies Used

* **Python**
* **Neo4j** – Knowledge Graph Database
* **FAISS** – Vector similarity search
* **Sentence Transformers** – Text embeddings
* **Streamlit** – User interface
* **PyVis** – Graph visualization
* **Ollama (Llama3)** – Local LLM for query generation and answers

---

# Dataset

The project uses the **IBM HR Employee Attrition dataset**:

`WA_Fn-UseC_-HR-Employee-Attrition.csv`

This dataset contains employee information such as:

* Age
* Department
* Job Role
* Education Field
* Business Travel
* Attrition status
* Monthly income

The dataset is transformed into a **knowledge graph**.

---

# Graph Schema

## Nodes

| Node Label     | Properties                                          |
| -------------- | --------------------------------------------------- |
| Employee       | employee_id, age, gender, monthly_income, job_level |
| Department     | name                                                |
| JobRole        | name                                                |
| EducationField | name                                                |
| BusinessTravel | type                                                |
| Attrition      | status                                              |

---

## Relationships

```
(Employee)-[:WORKS_IN]->(Department)
(Employee)-[:HAS_ROLE]->(JobRole)
(Employee)-[:STUDIED]->(EducationField)
(Employee)-[:TRAVELS]->(BusinessTravel)
(Employee)-[:HAS_ATTRITION]->(Attrition)
```

These relationships allow the system to perform **graph traversal reasoning**.

---

# Project Structure

```
RAG GRAPH PROJECT
│
├── app.py                     # Streamlit UI
├── rag_pipeline.py            # Main Graph RAG pipeline
├── query_generator.py         # Generates Cypher queries from questions
├── neo4j_executor.py          # Executes Neo4j queries
├── vector_store.py            # FAISS vector search
├── context_builder.py         # Formats graph context
├── answer_generator.py        # Generates final LLM answer
│
├── load_hr_graph.py           # Loads CSV data into Neo4j graph
├── create_employee_docs.py    # Creates text documents for vector store
│
├── employee_docs.json         # Documents used for vector search
├── graph.html                 # Generated graph visualization
│
├── WA_Fn-UseC_-HR-Employee-Attrition.csv  # HR dataset
```

---

# Graph Construction Pipeline

The graph is created from the HR dataset using `load_hr_graph.py`.

Process:

1. Load the HR dataset using **Pandas**
2. Create **Employee nodes**
3. Create related entity nodes:

   * Department
   * JobRole
   * EducationField
   * BusinessTravel
   * Attrition
4. Create relationships connecting employees to these entities.

Example Cypher pattern:

```
MERGE (e:Employee {employee_id: $employee_id})
MERGE (d:Department {name: $department})
MERGE (e)-[:WORKS_IN]->(d)
```

---

# Graph RAG Pipeline

The system answers questions using the following steps:

### Step 1 – User Question

User asks a question through the Streamlit interface.

### Step 2 – Cypher Query Generation

The LLM generates a **Cypher query** using the graph schema.

### Step 3 – Cypher Validation

The system validates and corrects Cypher queries to avoid schema errors.

### Step 4 – Graph Retrieval

Neo4j executes the query and retrieves **subgraphs using path traversal**.

### Step 5 – Vector Retrieval

FAISS retrieves relevant documents based on semantic similarity.

### Step 6 – Context Building

Graph data and vector documents are combined into a reasoning context.

### Step 7 – Answer Generation

The LLM generates a final answer using both **graph reasoning and document context**.

---

# Graph Explainability

The system provides transparency through:

* Generated **Cypher Query**
* Retrieved **Graph Paths**
* **Interactive graph visualization**
* Supporting **vector documents**

This allows users to understand **how the answer was derived**.

---

# Graph Visualization

The system uses **PyVis** to display graph results interactively.

Features:

* Node coloring by entity type
* Directed relationships
* Physics-based graph layout
* Interactive exploration

Visualization is displayed inside the **Streamlit interface**.

---

# Example Questions

Users can ask questions such as:

* "Show relationships of employees in Sales department"
* "Display a 2-hop graph of employees"
* "Which employees are connected to the Marketing department?"
* "Visualize employee relationships"

---

# How to Run the Project

### 1. Install dependencies

```
pip install -r requirements.txt
```

---

### 2. Start Neo4j

Ensure Neo4j is running locally:

```
bolt://localhost:7687
```

---

### 3. Load the HR graph

```
python load_hr_graph.py
```

---

### 4. Start the Streamlit app

```
streamlit run app.py
```

---

# Key Features

* Graph-based reasoning using **Neo4j**
* **Hybrid RAG architecture (Graph + Vector)**
* Automatic **Cypher query generation**
* **Cypher validation and correction**
* **Subgraph retrieval using k-hop traversal**
* **Interactive graph visualization**
* Fully **local LLM setup using Ollama**

---

# Future Improvements

* Support more complex graph reasoning queries
* Add graph analytics (centrality, community detection)
* Improve entity extraction from unstructured documents
* Deploy as a web service

---

# Conclusion

This project demonstrates how **Graph RAG systems combine knowledge graphs and vector search** to answer complex questions requiring relationship reasoning.

By integrating **Neo4j, FAISS, and LLMs**, the system provides **accurate, explainable, and interactive answers** beyond traditional vector-only RAG systems.
