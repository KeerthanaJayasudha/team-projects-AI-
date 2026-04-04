from backend.rag.rag_pipeline import ask_question

def test_rag_returns_results():
    response = ask_question("What is this website about?")
    assert response is not None