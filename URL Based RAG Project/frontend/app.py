import os
import sys
import streamlit as st
import requests
from urllib.parse import urlparse


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:
    from backend.utils.config import BACKEND_API_BASE, TOP_K
except Exception:
    
    BACKEND_API_BASE = "http://127.0.0.1:8000"
    TOP_K = 3

API_BASE = BACKEND_API_BASE.rstrip("/")


st.set_page_config(page_title="URL RAG Assistant", layout="wide")
st.title(" URL-Based RAG Assistant")


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {
            "detail": response.text if hasattr(response, "text") else "Unknown response error"
        }


def render_sources(sources):
    if not sources:
        return

    with st.expander(" Sources"):
        for source in sources:
            source_url = source.get("url", "")
            clickable_url = f"[Open Source]({source_url})" if source_url else "N/A"

            st.markdown(
                f"""
**Title:** {source.get('title','N/A')}  
**Section:** {source.get('section','N/A')}  
**Confidence:** {round(source.get('confidence',0),3)}  
{clickable_url}
"""
            )
            st.markdown("---")



if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "url_inputs" not in st.session_state:
    st.session_state.url_inputs = [""]

if "last_question" not in st.session_state:
    st.session_state.last_question = ""

if "last_eval_metrics" not in st.session_state:
    st.session_state.last_eval_metrics = None

if "search_scope" not in st.session_state:
    st.session_state.search_scope = "latest"



with st.sidebar:

    st.header(" System Controls")
    st.subheader(" Crawl Websites")

    for i in range(len(st.session_state.url_inputs)):

        col1, col2 = st.columns([4, 1])

        with col1:
            st.session_state.url_inputs[i] = st.text_input(
                f"URL {i+1}",
                value=st.session_state.url_inputs[i],
                key=f"url_{i}"
            )

        with col2:
            if st.button("Delete", key=f"remove_{i}"):
                if len(st.session_state.url_inputs) > 1:
                    st.session_state.url_inputs.pop(i)
                    st.rerun()

    if st.button(" Add URL"):
        st.session_state.url_inputs.append("")
        st.rerun()

    st.divider()

    max_depth = st.number_input("Max Depth", 1, 5, 2)
    max_pages = st.number_input("Max Pages", 1, 200, 20)

    update_strategy = st.selectbox(
        "Update Strategy",
        ["incremental", "force"]
    )

    st.session_state.search_scope = st.selectbox(
        "Search Scope",
        ["latest", "all"],
        index=0
    )

    
    if st.button("Start Crawling"):

        urls = [u.strip() for u in st.session_state.url_inputs if u.strip()]
        invalid_urls = [u for u in urls if not is_valid_url(u)]

        if not urls:
            st.warning("Please enter at least one URL.")

        elif invalid_urls:
            st.error("Invalid URL(s) detected:")
            for bad in invalid_urls:
                st.write(f"- {bad}")

        else:

            progress = st.progress(0, text="Preparing crawl request...")

            try:

                progress.progress(20, text="Sending crawl request...")

                response = requests.post(
                    f"{API_BASE}/crawl",
                    json={
                        "urls": urls,
                        "max_depth": max_depth,
                        "max_pages": max_pages,
                        "update_strategy": update_strategy
                    },
                    timeout=180
                )

                data = safe_json(response)

                progress.progress(100, text="Crawl finished")

                if response.status_code == 200:

                    st.success("Crawling Completed ")

                    st.write("Pages Crawled:", data.get("pages_crawled", 0))
                    st.write("Pages Processed:", data.get("pages_processed", 0))
                    st.write("Sections Updated:", data.get("sections_updated", 0))
                    st.write("Documents Indexed:", data.get("documents_indexed", 0))
                    st.write("Crawl ID:", data.get("crawl_id", "N/A"))

                else:
                    st.error(data.get("detail", "Crawling failed"))

            except requests.exceptions.ConnectionError:
                st.error("Backend not reachable. Start FastAPI server first.")

            except Exception as e:
                st.error(f"Backend error: {e}")

    st.divider()

    
    st.subheader(" System Status")

    if st.button("Check Status"):

        try:

            response = requests.get(f"{API_BASE}/status")

            status = safe_json(response)

            if response.status_code == 200:

                st.success("Backend Running")

                st.write("Documents Indexed:", status.get("documents_indexed", 0))
                st.write("Current Crawl ID:", status.get("current_crawl_id", "N/A"))

            else:
                st.error(status.get("detail", "Failed to fetch status"))

        except Exception:
            st.error("Backend not reachable")

    st.divider()

    
    st.subheader(" Retrieval Evaluation")

    if st.button("Evaluate Retrieval"):

        if not st.session_state.last_question:
            st.warning("Ask a question before evaluation.")

        else:

            try:

                eval_response = requests.post(
                    f"{API_BASE}/evaluate",
                    json={
                        "question": st.session_state.last_question,
                        "top_k": 3,
                        "search_scope": st.session_state.search_scope
                    }
                )

                metrics = safe_json(eval_response)

                if eval_response.status_code == 200:
                    st.session_state.last_eval_metrics = metrics
                else:
                    st.error(metrics.get("detail", "Evaluation failed"))

            except Exception as e:
                st.error(f"Evaluation failed: {e}")

    if st.session_state.last_eval_metrics:

        st.write("Precision@K:", st.session_state.last_eval_metrics.get("precision@k"))
        st.write("Recall@K:", st.session_state.last_eval_metrics.get("recall@k"))
        
    st.divider()

    if st.button(" Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.last_question = ""
        st.session_state.last_eval_metrics = None
        st.rerun()



st.header(" Ask Questions")

for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])
        render_sources(message.get("sources", []))


question = st.chat_input("Ask a question about the crawled websites...")

if question:

    st.session_state.last_question = question

    with st.chat_message("user"):
        st.markdown(question)

    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                response = requests.post(
                    f"{API_BASE}/query",
                    json={
                        "question": question,
                        "top_k": TOP_K if TOP_K <= 20 else 3,
                        "search_scope": st.session_state.search_scope
                    }
                )

                data = safe_json(response)

                if response.status_code != 200:
                    st.error(data.get("detail", "Query failed"))

                else:

                    answer = data.get("answer", "No answer generated")
                    sources = data.get("sources", [])

                    st.markdown(answer)
                    render_sources(sources)

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })

            except Exception as e:
                st.error(f"Error: {e}")