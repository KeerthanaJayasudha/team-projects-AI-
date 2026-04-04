import streamlit as st
import os
from src.rag import rag_answer
from src.loader import load_documents
from src.chunker import chunk_documents
from src.embedder import create_embeddings, reset_collection
from src.logger import get_logger
from src.config import RELEVANCE_THRESHOLD, RETRIEVAL_K, EMBEDDING_MODEL, LLM_MODEL

logger   = get_logger(__name__)
DATA_PATH = "data/"
os.makedirs(DATA_PATH, exist_ok=True)

# ──────────────────────────────────────────────────────────
# POLICY REGISTRY — edit this dict to match your documents
# ──────────────────────────────────────────────────────────
POLICY_REGISTRY = {
    "Acceptable-Use-Policy.pdf": {
        "label":   "Acceptable Use Policy",
        "type":    "IT Security",
        "version": "v2.3",
        "date":    "Apr 2024",
        "dept":    "CTS",
        "org":     "Illinois Tech",
        "scope":   "Students, Faculty, Staff",
    },
    "acceptable-use-university-computers.pdf": {
        "label":   "Acceptable Use — University Computers",
        "type":    "IT Policy",
        "version": "IT-PO-1500",
        "date":    "Feb 2023",
        "dept":    "ITS",
        "org":     "Radford University",
        "scope":   "All Users",
    },
    "aup.pdf": {
        "label":   "Acceptable Use Policy",
        "type":    "Acceptable Use",
        "version": "v1.0",
        "date":    "Jun 2013",
        "dept":    "ITS",
        "org":     "Univ. of Virgin Islands",
        "scope":   "All Stakeholders",
    },
    "Policy_ComputerUsage.pdf": {
        "label":   "Computer Usage Policy",
        "type":    "Computer Use",
        "version": "v1.0",
        "date":    "Dec 2000",
        "dept":    "IST",
        "org":     "Fairleigh Dickinson",
        "scope":   "Faculty, Staff, Students",
    },
    "SUNYOPT_IT_Acceptable_Use_Policy.pdf": {
        "label":   "IT Acceptable Use Policy",
        "type":    "IT Policy",
        "version": "v1.0",
        "date":    "Jun 2024",
        "dept":    "IT Services",
        "org":     "SUNY Optometry",
        "scope":   "All Users",
    },
    "uni_utah_financial_conflict.pdf": {
        "label":   "Individual Financial Conflict of Interest Policy",
        "type":    "Research Compliance",
        "version": "Rev. 15",
        "date":    "Jul 2024",
        "dept":    "Office of Research",
        "org":     "University of Utah",
        "scope":   "All Investigators & Employees",
    },
    "uni_utah.pdf": {
        "label":   "Firearms on Campus Policy",
        "type":    "Campus Safety",
        "version": "Rev. 0",
        "date":    "Sep 2007",
        "dept":    "Office of General Counsel",
        "org":     "University of Utah",
        "scope":   "Faculty, Staff, Students",
    },
    "regent_uni_aup.pdf": {
        "label":   "Acceptable Use Policy",
        "type":    "IT Security",
        "version": "v1.3",
        "date":    "Aug 2024",
        "dept":    "Information Security",
        "org":     "Regent University",
        "scope":   "Staff, Faculty, Students, Third Parties",
    },
    "Acceptable-Use-Policy_-new_uni.pdf": {
        "label":   "Acceptable Use Policy",
        "type":    "IT Policy",
        "version": "v2019",
        "date":    "Jun 2019",
        "dept":    "OIT",
        "org":     "Mount Saint Mary's University",
        "scope":   "Faculty, Staff, Students",
    },
}

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Enterprise Policy Q&A",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# ─────────────────────────────────────────────
# CSS — Bloomberg Terminal × Legal System
# Amber accent, near-black bg, mono data layer
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Lora:wght@400;500&display=swap');

:root {
    --bg:        #ffffff;
    --surface:   #f9fafb;
    --surface2:  #f3f4f6;
    --border:    #e5e7eb;
    --border2:   #d1d5db;
    --text:      #111827;
    --muted:     #6b7280;
    --muted2:    #9ca3af;
    --amber:     #d97706;
    --amber-dim: #fef3c7;
    --amber-glow:#f59e0b;
    --green:     #16a34a;
    --green-dim: #dcfce7;
    --red:       #dc2626;
    --red-dim:   #fee2e2;
    --blue:      #2563eb;
    --teal:      #0d9488;
}

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Lora', Georgia, serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stMetric label { color: var(--muted) !important; font-size: 0.68rem !important; }
[data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.4rem !important;
    color: var(--amber) !important;
}

/* ── Section labels ── */
.slabel {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--amber);
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px;
    margin-bottom: 10px;
    display: block;
}

/* ── Policy registry card ── */
.preg-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 2px solid var(--amber);
    border-radius: 4px;
    padding: 9px 12px;
    margin-bottom: 7px;
    cursor: default;
    transition: border-color 0.12s, background 0.12s;
}
.preg-card:hover { border-left-color: var(--amber-glow); background: #fef9ee; }
.preg-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--text);
    margin-bottom: 5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.preg-tags { display: flex; gap: 5px; flex-wrap: wrap; }
.ptag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    background: var(--bg);
    border: 1px solid var(--border2);
    border-radius: 2px;
    padding: 1px 5px;
    color: var(--muted);
}
.ptag-type { border-color: var(--amber-dim); color: var(--amber); }

/* ── Header ── */
.hero-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
    color: var(--amber);
    text-transform: uppercase;
    margin-bottom: 6px;
}
.hero-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.6rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1.05;
    letter-spacing: -1px;
    margin-bottom: 8px;
}
.hero-title span { color: var(--amber); }
.hero-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 1px;
    line-height: 1.9;
}

/* ── Index status pill ── */
.idx-ready {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    background: var(--green-dim);
    border: 1px solid var(--green);
    color: var(--green);
    border-radius: 3px;
    padding: 5px 12px;
    display: inline-block;
}
.idx-notready {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    background: var(--amber-dim);
    border: 1px solid var(--amber);
    color: var(--amber);
    border-radius: 3px;
    padding: 5px 12px;
    display: inline-block;
}

/* ── Query block ── */
.q-wrap {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--blue);
    border-radius: 6px;
    padding: 14px 18px;
    margin: 16px 0 2px 0;
}
.q-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--muted2);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.q-text {
    font-size: 1rem;
    color: var(--text);
    font-family: 'Lora', serif;
}

/* ── Answer block — CITED ── */
.a-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 18px 20px;
    margin: 2px 0 6px 0;
    position: relative;
    overflow: hidden;
}
.a-wrap::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px;
    height: 100%;
    background: var(--green);
}
.a-verdict {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--green);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.a-verdict::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}
.a-text {
    font-family: 'Lora', serif;
    font-size: 0.97rem;
    color: var(--text);
    line-height: 1.75;
    margin-bottom: 14px;
}

/* ── Refused block ── */
.r-wrap {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 18px 20px;
    margin: 2px 0 6px 0;
    position: relative;
    overflow: hidden;
}
.r-wrap::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px;
    height: 100%;
    background: var(--red);
}
.r-verdict {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--red);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.r-verdict::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}
.r-reason {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--muted);
    line-height: 1.8;
    background: var(--red-dim);
    border: 1px solid #fca5a5;
    border-radius: 4px;
    padding: 10px 14px;
}
.r-guarantee {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: var(--muted2);
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid var(--border);
}

/* ── Citation panel ── */
.cite-panel {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 10px 14px;
    margin-bottom: 12px;
}
.cite-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 2px;
    color: var(--amber);
    text-transform: uppercase;
    margin-bottom: 8px;
}
.cite-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 5px 0;
    border-bottom: 1px solid var(--border);
}
.cite-item:last-child { border-bottom: none; }
.cite-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--amber);
    min-width: 20px;
}
.cite-doc {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--teal);
    flex: 1;
}
.cite-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: var(--muted);
}

/* ── Score panel ── */
.score-panel {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 0;
}
.score-block {
    font-family: 'JetBrains Mono', monospace;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 6px 12px;
    min-width: 110px;
}
.score-key {
    font-size: 0.55rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted2);
    margin-bottom: 3px;
}
.score-val {
    font-size: 1rem;
    font-weight: 500;
}
.sv-green  { color: var(--green); }
.sv-yellow { color: #facc15; }
.sv-red    { color: var(--red); }
.sv-blue   { color: var(--blue); }
.sv-muted  { color: var(--muted); }

/* ── Confidence bar ── */
.conf-track {
    height: 3px;
    background: var(--border2);
    border-radius: 2px;
    margin-top: 4px;
    overflow: hidden;
}
.conf-fill { height: 100%; border-radius: 2px; }

/* ── Chunk debug table ── */
.chunk-tbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    width: 100%;
    border-collapse: collapse;
}
.chunk-tbl th {
    font-size: 0.58rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted2);
    border-bottom: 1px solid var(--border);
    padding: 4px 8px;
    text-align: left;
}
.chunk-tbl td {
    padding: 6px 8px;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
    color: var(--muted);
}
.chunk-tbl tr.chosen td { color: var(--text); background: #fefce8; }
.chunk-tbl tr:last-child td { border-bottom: none; }
.td-rank    { color: var(--amber) !important; font-weight: 500; }
.td-chosen  { color: var(--green) !important; }
.td-skipped { color: var(--muted2) !important; }
.td-dist    { color: #facc15 !important; }
.td-src     { color: var(--teal) !important; }
.td-prev    { font-size: 0.62rem; color: var(--muted2) !important;
              max-width: 280px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ── Input ── */
.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 5px !important;
    color: var(--text) !important;
    font-family: 'Lora', serif !important;
    font-size: 0.95rem !important;
    padding: 11px 15px !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 2px rgba(245,158,11,0.12) !important;
}
.stTextInput > div > div > input:disabled { opacity: 0.3 !important; }
.stTextInput > div > div > input::placeholder { color: var(--muted2) !important; }
.stTextInput label { display: none !important; }

/* ── Buttons ── */
.stButton > button {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 5px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.5px !important;
    transition: all 0.12s !important;
}
.stButton > button:hover {
    background: #fef3c7 !important;
    border-color: var(--amber) !important;
    color: var(--amber) !important;
}
.stButton > button:disabled { opacity: 0.25 !important; }

/* ── Expander ── */
details summary {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: var(--muted2) !important;
}
details[open] summary { color: var(--amber) !important; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 56px 0;
}
.empty-icon {
    font-size: 2.8rem;
    margin-bottom: 14px;
    opacity: 0.18;
}
.empty-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
    color: var(--muted2);
    margin-bottom: 6px;
}
.empty-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 1.5px;
    color: var(--muted2);
    opacity: 0.6;
    text-transform: uppercase;
}

/* ── Warn banner ── */
.warn-banner {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    background: var(--amber-dim);
    border: 1px solid var(--amber);
    color: var(--amber);
    border-radius: 4px;
    padding: 8px 14px;
    margin-bottom: 10px;
}


/* ── Agent trace ── */
.agent-trace {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 10px 14px;
    margin-top: 8px;
}
.agent-trace-header {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 2.5px;
    color: var(--amber);
    text-transform: uppercase;
    margin-bottom: 8px;
}
.agent-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 6px 0;
    border-bottom: 1px solid var(--border);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
}
.agent-row:last-child { border-bottom: none; }
.agent-name {
    min-width: 160px;
    color: var(--teal);
    font-weight: 500;
}
.agent-arrow { color: var(--muted2); }
.agent-output { color: var(--amber); font-weight: 500; min-width: 130px; }
.agent-detail { color: var(--muted); font-size: 0.62rem; }

/* Rewrite notice */
.rewrite-notice {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    background: #fffbeb;
    border: 1px solid var(--amber-dim);
    border-radius: 4px;
    padding: 6px 12px;
    color: var(--amber);
    margin-top: 6px;
    margin-bottom: 4px;
}

/* Greeting / out-of-scope */
.greeting-block {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--teal);
    border-radius: 6px;
    padding: 14px 18px;
    margin: 2px 0 6px 0;
    font-size: 0.95rem;
    font-family: 'Lora', serif;
    color: var(--text);
}
.greeting-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 2px;
    color: var(--teal);
    text-transform: uppercase;
    margin-bottom: 8px;
}

hr { border-color: var(--border) !important; }
#MainMenu, footer, header { visibility: hidden; }

/* Force sidebar always visible */
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: flex !important; transform: none !important; min-width: 280px !important; }

/* Remove streamlit's default padding */
.block-container { padding-top: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# INDEX EXISTENCE CHECK
# ─────────────────────────────────────────────
def index_exists():
    """Check if ChromaDB already has a built collection with chunks."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path="vector_db")
        col    = client.get_collection("enterprise_rag")
        return col.count() > 0
    except Exception:
        return False

def build_index_now():
    docs   = load_documents()
    chunks = chunk_documents(docs)
    reset_collection()
    create_embeddings(chunks)
    return len(docs), len(chunks)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in [
    ("messages", []),
    ("index_built", False),
    ("last_q", ""),
    ("input_key", 0),
    ("n_queries", 0),
    ("n_answered", 0),
    ("n_refused", 0),
    ("auto_build_done", False),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Auto-build on startup if index doesn't exist ──
if not st.session_state.auto_build_done:
    st.session_state.auto_build_done = True
    if index_exists():
        # Index already built — just mark as ready
        st.session_state.index_built = True
        logger.info("Existing index detected — skipping auto-build.")
    else:
        # No index found — build silently in background
        logger.info("No index found — auto-building on startup...")
        try:
            with st.spinner("Building index for the first time — please wait..."):
                ndocs, nchunks = build_index_now()
                st.session_state.index_built = True
                logger.info(f"Auto-build complete: {nchunks} chunks from {ndocs} pages")
        except Exception as e:
            logger.error(f"Auto-build failed: {e}")
            st.error(f"Auto-build failed: {e}")


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_data_pdfs():
    return sorted([f for f in os.listdir(DATA_PATH) if f.lower().endswith(".pdf")])

def get_meta(fname):
    return POLICY_REGISTRY.get(fname, {
        "label": fname, "type": "Policy", "version": "—",
        "date": "—", "dept": "—", "org": "—", "scope": "—"
    })

def conf_style(c):
    if c >= 0.6:  return "sv-green",  "#4ade80"
    if c >= 0.4:  return "sv-yellow", "#facc15"
    return "sv-red", "#f87171"

def get_chunk_debug(question):
    from src.retriever import retrieve
    results        = retrieve(question)
    docs           = results["documents"][0]
    metas          = results["metadatas"][0]
    scores         = results["distances"][0]
    qw             = set(question.lower().split())
    chunks = []
    for doc, meta, score in zip(docs, metas, scores):
        overlap = len(qw & set(doc.lower().split()))
        fname   = os.path.basename(meta.get("source","?")) if meta else "?"
        page    = (meta.get("page",0) or 0)+1 if meta else "?"
        m       = get_meta(fname)
        chunks.append({
            "distance": score, "overlap": overlap,
            "source": fname, "page": page,
            "type": m.get("type","—"), "org": m.get("org","—"),
            "preview": doc[:150].strip().replace("\n"," ")
        })
    chunks.sort(key=lambda x: (x["distance"], -x["overlap"]))
    return chunks

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="slabel">Enterprise RAG — Capstone I</span>', unsafe_allow_html=True)

    # Session counters
    c1, c2, c3 = st.columns(3)
    c1.metric("Queries",  st.session_state.n_queries)
    c2.metric("Cited",    st.session_state.n_answered)
    c3.metric("Refused",  st.session_state.n_refused)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="slabel">Policy Registry</span>', unsafe_allow_html=True)

    pdfs = get_data_pdfs()
    for pdf in pdfs:
        m = get_meta(pdf)
        st.markdown(f"""
        <div class="preg-card">
            <div class="preg-name" title="{pdf}">📄 {m['label']}</div>
        </div>
        """, unsafe_allow_html=True)

    if not pdfs:
        st.markdown('<span style="color:#52525b;font-size:0.75rem;font-family:JetBrains Mono,monospace;">No PDFs in data/</span>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<span class="slabel">System</span>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style='font-family:JetBrains Mono,monospace;font-size:0.68rem;
                color:#52525b;line-height:2.2;'>
    LLM &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#a1a1aa'>{LLM_MODEL}</span><br>
    Embeddings &nbsp;<span style='color:#a1a1aa'>{EMBEDDING_MODEL}</span><br>
    Reranker &nbsp;&nbsp;&nbsp;<span style='color:#a1a1aa'>ms-marco-MiniLM-L6</span><br>
    Retrieval-K &nbsp;<span style='color:#a1a1aa'>{RETRIEVAL_K}</span><br>
    Threshold &nbsp;&nbsp;<span style='color:#a1a1aa'>{RELEVANCE_THRESHOLD}</span><br>
    Hallucination &nbsp;<span style='color:#4ade80'>BLOCKED ✓</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    ba, bb = st.columns(2)
    with ba:
        if st.button("⟳ Rebuild", use_container_width=True, help="Only needed when you add new PDFs"):
            prog = st.progress(0, text="Initialising...")
            try:
                prog.progress(15, text="Loading PDFs...")
                prog.progress(40, text="Chunking documents...")
                prog.progress(60, text="Resetting vector store...")
                prog.progress(75, text="Embedding chunks...")
                ndocs, nchunks = build_index_now()
                prog.progress(100, text="Done.")
                st.session_state.index_built = True
                logger.info(f"Index rebuilt: {nchunks} chunks / {ndocs} pages")
                st.success(f"✓ {nchunks} chunks")
                st.rerun()
            except Exception as e:
                prog.empty()
                st.error(str(e))
                logger.error(f"Build error: {e}")
    with bb:
        if st.button("✕ Clear Chat", use_container_width=True):
            for k in ["messages","last_q","n_queries","n_answered","n_refused"]:
                st.session_state[k] = [] if k == "messages" else ("" if k == "last_q" else 0)
            st.rerun()


# ─────────────────────────────────────────────
# MAIN — HEADER
# ─────────────────────────────────────────────
hA, hB = st.columns([3, 1])

with hA:
    st.markdown('<div class="hero-eyebrow">Evidence-First RAG · No Hallucination Guarantee</div>',
                unsafe_allow_html=True)
    st.markdown("""
    <div class="hero-title">Enterprise Policy<br><span>Q&A System</span></div>
    <div class="hero-sub">
    HR &nbsp;·&nbsp; IT Security &nbsp;·&nbsp; Compliance &nbsp;·&nbsp; Acceptable Use<br>
    All answers grounded in indexed documents &nbsp;·&nbsp; Citations required
    </div>
    """, unsafe_allow_html=True)

with hB:
    st.markdown("<br><br>", unsafe_allow_html=True)
    pdfs_now = get_data_pdfs()
    if st.session_state.index_built:
        st.markdown(
            f'<div class="idx-ready">● INDEX READY &nbsp;|&nbsp; {len(pdfs_now)} DOC{"S" if len(pdfs_now)!=1 else ""}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="idx-notready">○ INDEX NOT BUILT</div>',
            unsafe_allow_html=True
        )

st.markdown("---")

# ─────────────────────────────────────────────
# CHAT AREA
# ─────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">⚖</div>
        <div class="empty-title">No queries yet</div>
        <div class="empty-sub">Ask a policy question to retrieve cited answers</div>
    </div>
    """, unsafe_allow_html=True)

for idx, msg in enumerate(st.session_state.messages):

    # ── USER QUERY ──
    if msg["role"] == "user":
        qnum = (idx // 2) + 1
        st.markdown(f"""
        <div class="q-wrap">
            <div class="q-meta">Query #{qnum:02d} &nbsp;·&nbsp; Natural Language</div>
            <div class="q-text">{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── ASSISTANT RESPONSE ──
    elif msg["role"] == "assistant":
        result      = msg["result"]
        answer      = result["answer"]
        sources     = result["sources"]
        conf        = result["confidence"]
        dist        = result["distance"]
        refused     = answer.startswith("REFUSED")
        chunks      = msg.get("chunks", [])
        intent      = result.get("intent", "POLICY_QUESTION")
        rewritten   = result.get("rewritten")
        validation  = result.get("validation")
        agent_trace = result.get("agent_trace", [])
        is_greeting = intent in ("GREETING", "OUT_OF_SCOPE")

        if is_greeting:
            # ───── GREETING / OUT OF SCOPE ─────
            label = "Greeting Response" if intent == "GREETING" else "Out of Scope"
            st.markdown(f"""
            <div class="greeting-block">
                <div class="greeting-label">&#9675; &nbsp; {label}</div>
                {answer}
            </div>
            """, unsafe_allow_html=True)

        elif refused:
            # ───── REFUSED ANSWER ─────
            val_reason = ""
            if validation and validation.get("verdict") == "HALLUCINATED":
                val_reason = f"<br><br>Validator verdict: <strong>HALLUCINATED</strong> — {validation.get('reason','')}"
            guarantee_text = f"HALLUCINATION CONTROL &nbsp;&middot;&nbsp; No free-text generation without grounded evidence &nbsp;&middot;&nbsp; Threshold enforced at distance {RELEVANCE_THRESHOLD}"
            reason_text = f"No relevant policy content found in the indexed document corpus.<br><br>Best retrieval distance: <strong>{dist if dist else chr(8212)}</strong> &nbsp;(threshold: {RELEVANCE_THRESHOLD})<br>This system does not generate answers without verified citations.{val_reason}"
            st.markdown(
                f'<div class="r-wrap">'
                f'<div class="r-verdict">&#8856; &nbsp; Refused &mdash; Outside Policy Scope</div>'
                f'<div class="r-reason">' + reason_text + '</div>'
                f'<div class="r-guarantee">' + guarantee_text + '</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        else:
            # ───── CITED ANSWER ─────
            cls, hex_col = conf_style(conf)
            conf_pct = int(conf * 100)

            # Answer block
            st.markdown(f"""
            <div class="a-wrap">
                <div class="a-verdict">&#10003; &nbsp; Policy Answer — Cited &amp; Verified</div>
                <div class="a-text">{answer}</div>
            </div>
            """, unsafe_allow_html=True)

            # Citations — rendered in separate calls to avoid Streamlit escaping nested HTML
            st.markdown('<div class="cite-panel"><div class="cite-header">Source Citations</div>',
                        unsafe_allow_html=True)
            for ci, src in enumerate(sources):
                st.markdown(
                    f'<div class="cite-item">'
                    f'<span class="cite-num">[{ci+1}]</span>'
                    f'<span class="cite-doc">&#128206; {src}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

            # Score panel
            st.markdown(f"""
            <div class="score-panel">
                <div class="score-block">
                    <div class="score-key">Confidence</div>
                    <div class="score-val {cls}">{conf} ({conf_pct}%)</div>
                    <div class="conf-track">
                        <div class="conf-fill" style="width:{conf_pct}%;background:{hex_col};"></div>
                    </div>
                </div>
                <div class="score-block">
                    <div class="score-key">Distance</div>
                    <div class="score-val sv-blue">{dist}</div>
                </div>
                <div class="score-block">
                    <div class="score-key">Grounding</div>
                    <div class="score-val sv-green">CITED</div>
                </div>
                <div class="score-block">
                    <div class="score-key">Hallucination</div>
                    <div class="score-val sv-green">BLOCKED</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── RETRIEVAL DEBUG EXPANDER — backend only, hidden from UI ──
        if False and chunks and not is_greeting:
            with st.expander(f"▸ Retrieval Evidence — {len(chunks)} chunks · {sum(1 for c in chunks[:3])} chosen"):
                rows_html = ""
                for i, c in enumerate(chunks):
                    chosen    = i < 3
                    row_cls   = "chosen" if chosen else ""
                    st_str    = '<span class="td-chosen">● CHOSEN</span>' if chosen else '<span class="td-skipped">○ skipped</span>'
                    c_conf    = round(1 - c["distance"], 2)
                    cc, _     = conf_style(c_conf)

                    rows_html += f"""
                    <tr class="{row_cls}">
                        <td class="td-rank">#{i+1:02d}</td>
                        <td>{st_str}</td>
                        <td class="td-dist">{round(c['distance'],3)}</td>
                        <td class="{cc}">{c_conf}</td>
                        <td style="color:#89dceb">{c['overlap']}w</td>
                        <td class="td-src">{c['source']}</td>
                        <td style="color:#a1a1aa">p.{c['page']}</td>
                        <td style="color:#71717a">{c['type']}</td>
                        <td class="td-prev">{c['preview']}</td>
                    </tr>"""

                st.markdown(f"""
                <table class="chunk-tbl">
                    <thead>
                        <tr>
                            <th>Rank</th><th>Status</th><th>Distance</th>
                            <th>Conf.</th><th>Overlap</th><th>Source</th>
                            <th>Page</th><th>Type</th><th>Preview</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
                """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INPUT BAR
# ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

if not st.session_state.index_built:
    st.markdown(
        '<div class="warn-banner">⚠ &nbsp; Index is being built — please wait a moment before querying.</div>',
        unsafe_allow_html=True
    )

i1, i2 = st.columns([7, 1])
with i1:
    question = st.text_input(
        label="q",
        placeholder='e.g. "Can users share their passwords?"' if st.session_state.index_built else "Build index first...",
        disabled=not st.session_state.index_built,
        key=f"q_input_{st.session_state.input_key}"
    )
with i2:
    ask = st.button("Ask →", use_container_width=True,
                    disabled=not st.session_state.index_built)

st.markdown("""
<div style='font-family:JetBrains Mono,monospace;font-size:0.6rem;
            color:#3f3f46;text-align:center;margin-top:8px;letter-spacing:1px;'>
    ENTERPRISE POLICY Q&A &nbsp;·&nbsp; RAG + CITATION ENFORCEMENT &nbsp;·&nbsp;
    NO FREE-TEXT HALLUCINATION &nbsp;·&nbsp; CAPSTONE I
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HANDLE QUERY
# ─────────────────────────────────────────────
if st.session_state.index_built and ask and question.strip():
    if question != st.session_state.last_q:
        st.session_state.last_q   = question
        st.session_state.n_queries += 1

        st.session_state.messages.append({"role": "user", "content": question})

        with st.spinner("Retrieving policy evidence..."):
            try:
                result = rag_answer(question)
                chunks = get_chunk_debug(question)
            except Exception as e:
                result = {"answer": f"REFUSED: System error — {e}",
                          "sources": [], "confidence": 0, "distance": None}
                chunks = []
                logger.error(f"Query error: {e}")

        if result["answer"].startswith("REFUSED"):
            st.session_state.n_refused  += 1
        else:
            st.session_state.n_answered += 1

        st.session_state.messages.append({
            "role": "assistant", "result": result, "chunks": chunks
        })
        st.session_state.input_key += 1
        st.rerun()