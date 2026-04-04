# Cypher Query Validation and Correction

## Overview
Added automatic Cypher query validation and correction to fix common schema mistakes before executing queries against Neo4j.

## Problem
The LLM sometimes generates Cypher queries that don't match the graph schema, causing query failures or incorrect results.

### Common Mistakes
1. **Wrong node type with properties**: `Employee {name:"Sales"}` instead of `Department {name:"Sales"}`
2. **Wrong relationship endpoints**: `Department -[:HAS_ROLE]-> JobRole` instead of `Employee -[:HAS_ROLE]-> JobRole`
3. **Reversed relationship direction**: `Department -[:WORKS_IN]-> Employee` instead of `Employee -[:WORKS_IN]-> Department`
4. **Bidirectional relationships**: `Employee -[:WORKS_IN]- Department` instead of `Employee -[:WORKS_IN]-> Department`
5. **Invalid property names**: `JobRole {title:...}` instead of `JobRole {name:...}`

## Solution
Added `validate_and_correct_cypher()` function in `rag_pipeline.py` that automatically detects and fixes these issues.

## Implementation

### Location
File: `rag_pipeline.py`

### Function
```python
def validate_and_correct_cypher(cypher):
    """
    Validates and corrects common Cypher query mistakes based on schema.
    """
```

### Integration
The validation is called in `ask_question()` immediately after `generate_cypher()`:

```python
# Step 1 — Generate Cypher
cypher = generate_cypher(question, schema)

# Step 2 — Validate and Correct Cypher
cypher = validate_and_correct_cypher(cypher)

# Step 3 — Query Neo4j
graph_data = run_cypher_query(cypher)
```

## Corrections Applied

### 1. Employee with Department Name
**Pattern**: `(:Employee {name:"Sales"})`  
**Correction**: `(:Department {name:"Sales"})`  
**Reason**: Employee nodes don't have a "name" property; Department nodes do

### 2. Department with Employee Relationships
**Patterns**:
- `(d:Department)-[:HAS_ROLE]->(j:JobRole)` → `(e:Employee)-[:HAS_ROLE]->(j:JobRole)`
- `(d:Department)-[:STUDIED]->(e:EducationField)` → `(e:Employee)-[:STUDIED]->(e:EducationField)`
- `(d:Department)-[:TRAVELS]->(b:BusinessTravel)` → `(e:Employee)-[:TRAVELS]->(b:BusinessTravel)`
- `(d:Department)-[:HAS_ATTRITION]->(a:Attrition)` → `(e:Employee)-[:HAS_ATTRITION]->(a:Attrition)`

**Reason**: These relationships connect to Employee, not Department

### 3. Reversed WORKS_IN Direction
**Pattern**: `(:Department)-[:WORKS_IN]->(:Employee)`  
**Correction**: `(:Employee)-[:WORKS_IN]->(:Department)`  
**Reason**: Employees work in departments, not the other way around

### 4. Bidirectional to Directional
**Pattern**: `(:Employee)-[:WORKS_IN]-(:Department)`  
**Correction**: `(:Employee)-[:WORKS_IN]->(:Department)`  
**Reason**: WORKS_IN is a directed relationship

### 5. Invalid Property Names
**Patterns**:
- `JobRole {title:...}` → `JobRole {name:...}`
- `Department {dept_name:...}` → `Department {name:...}`

**Reason**: Schema uses "name" property consistently

### 6. Remove Invalid Properties
**Pattern**: `(:Employee {name:"John"})`  
**Correction**: `(:Employee)`  
**Reason**: Employee nodes don't have a "name" property (they have employee_id)

## Features

### Variable Preservation
The validator preserves variable names when correcting queries:
- `(e:Employee {name:"Sales"})` → `(e:Department {name:"Sales"})`
- `(d:Department)-[:HAS_ROLE]->(j:JobRole)` → `(d:Employee)-[:HAS_ROLE]->(j:JobRole)`

### User Feedback
When corrections are applied, the system prints a summary:
```
⚠️  Cypher Query Corrections Applied:
   - Fixed: Employee {name:"Sales"} → Department {name:"Sales"}
   - Fixed: Department -[:HAS_ROLE]-> JobRole → Employee -[:HAS_ROLE]-> JobRole
```

### Non-Invasive
- Only modifies queries that have schema violations
- Correct queries pass through unchanged
- Preserves query structure and logic

## Schema Reference

### Nodes and Properties
```
Employee: employee_id, age, gender, monthly_income, job_level
Department: name
JobRole: name
EducationField: name
BusinessTravel: type
Attrition: status
```

### Valid Relationships
```
(Employee)-[:WORKS_IN]->(Department)
(Employee)-[:HAS_ROLE]->(JobRole)
(Employee)-[:STUDIED]->(EducationField)
(Employee)-[:TRAVELS]->(BusinessTravel)
(Employee)-[:HAS_ATTRITION]->(Attrition)
```

## Testing

Tested with 8 different scenarios covering:
- ✅ Employee with department name property
- ✅ Department with employee relationships
- ✅ Multiple department names (Sales, HR, etc.)
- ✅ Reversed relationship directions
- ✅ Bidirectional relationships
- ✅ Complex queries with multiple errors
- ✅ Correct queries (no changes)

## Benefits

1. **Improved Reliability**: Queries are automatically corrected before execution
2. **Better User Experience**: Users get correct results even when LLM makes mistakes
3. **Reduced Errors**: Fewer Neo4j query failures
4. **Transparent**: Users can see what corrections were applied
5. **Maintainable**: Easy to add new correction rules as needed

## Limitations

- Only fixes known common patterns
- Complex multi-clause queries with interdependent errors may need multiple passes
- Doesn't validate semantic correctness (e.g., whether a department name exists)
- Relies on regex patterns which may not catch all edge cases

## Future Enhancements

Potential improvements:
1. Add validation against actual Neo4j schema using `CALL db.schema.visualization()`
2. Implement multi-pass correction for complex queries
3. Add property value validation (e.g., check if department name exists)
4. Log corrections for analysis and LLM prompt improvement
5. Add user configuration for correction strictness
