import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Text-to-SQL Multi-Agent", page_icon="🧠", layout="wide")
st.title("🧠 Text-to-SQL Multi-Agent System")

# --- Initialize session state ---
if 'clear_input' not in st.session_state:
    st.session_state.clear_input = False
if 'last_results' not in st.session_state:
    st.session_state.last_results = None

# --- Input Section ---
# Clear input if flag is set
if st.session_state.clear_input:
    default_value = ""
    st.session_state.clear_input = False
else:
    default_value = ""

query = st.text_input("Enter your natural language query:", value=default_value)
run_button = st.button("Run Query")

if run_button and query:
    # Use the non-streaming endpoint for faster response
    url = "http://localhost:8000/query"
    
    # Show processing indicator
    with st.spinner("Processing your query..."):
        try:
            response = requests.post(url, json={"query": query, "session_id": "demo_session"}, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Store results in session state
            st.session_state.last_results = data
            st.session_state.clear_input = True
            
            st.success("✅ Query completed successfully.")
            
        except requests.exceptions.Timeout:
            st.error("⚠️ Request timed out. Please try again.")
            st.session_state.last_results = None
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Error: {str(e)}")
            st.session_state.last_results = None

# --- Display Results ---
if st.session_state.last_results:
    data = st.session_state.last_results
    
    # Extract data from response
    sql_text = ""
    explanation_text = ""
    result_df = None
    
    # Get pipeline stages for display
    pipeline = data.get("pipeline", [])
    
    # --- Pipeline Visualization ---
    if pipeline:
        st.subheader("🔄 Pipeline Stages")
        
        for stage in pipeline:
            stage_name = stage.get("stage", "")
            description = stage.get("description", "")
            
            with st.expander(f"**{stage_name}**", expanded=False):
                if stage_name == "Query Rewriter":
                    st.write("**Rewritten Query:**")
                    st.info(description)
                    explanation = stage.get("explanation", "")
                    if explanation:
                        st.write("**Explanation:**")
                        st.write(explanation)
                
                elif stage_name == "Schema Retrieval":
                    st.write(description)
                    summary = stage.get("summary", "")
                    if summary:
                        st.write("**Summary:**")
                        st.write(summary)
                
                elif stage_name == "Query Generation":
                    st.code(description, language="sql")
                    sql_text = description
                
                elif stage_name == "Validation":
                    st.write(description)
                    details = stage.get("details", {})
                    if details:
                        st.json(details)
                
                elif stage_name == "Query Execution":
                    st.write(description)
                    exec_time = stage.get("execution_time", 0)
                    if exec_time:
                        st.write(f"**Execution Time:** {exec_time}s")
                
                elif stage_name == "Natural Language Explanation":
                    st.markdown(description)
                    explanation_text = description
    
    # Get query results
    rows = data.get("rows", [])
    columns = data.get("columns", [])
    
    if rows and columns:
        result_df = pd.DataFrame(rows, columns=columns)
    
    # --- Final Output Display ---
    if sql_text:
        st.subheader("🧮 Generated SQL")
        st.code(sql_text, language="sql")

    if result_df is not None and not result_df.empty:
        st.subheader("📊 Results")
        st.dataframe(result_df, use_container_width=True)
    else:
        st.warning("⚠️ No data returned for this query.")

    if explanation_text:
        st.subheader("💡 Insights")
        st.markdown(explanation_text)
