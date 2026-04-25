"""
Streamlit RAG Chatbot — SharePoint Demo
========================================
A production-like demo using LlamaIndex + FAISS + Ollama.
"""

from __future__ import annotations

import logging
import os
import sys

import streamlit as st

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Contoso SharePoint Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from app.connectors.mock_connector import load_mock_documents  # noqa: E402
from app.rag.indexer import get_or_build_index, build_index  # noqa: E402
from app.rag.retriever import build_query_engine, query as rag_query  # noqa: E402

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
INDEX_DIR = os.environ.get("INDEX_DIR", "/app/.index")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
TOP_K = int(os.environ.get("TOP_K", "4"))
STRICT_GROUNDED = os.environ.get("STRICT_GROUNDED", "true").lower() == "true"


# ---------------------------------------------------------------------------
# Helper: render sources expander
# ---------------------------------------------------------------------------
def render_sources(sources: list[dict]) -> None:
    """Render a Sources expander with SharePoint metadata cards."""
    if not sources:
        return
    with st.expander(f"📚 Sources ({len(sources)} document(s))", expanded=False):
        for i, src in enumerate(sources, 1):
            cols = st.columns([4, 1])
            with cols[0]:
                st.markdown(
                    f"**{i}. [{src['title']}]({src['source_url']})**  \n"
                    f"📁 **Library:** {src['library']} &nbsp;·&nbsp; "
                    f"👤 **Owner:** {src['owner']} &nbsp;·&nbsp; "
                    f"🗓️ **Modified:** {src['last_modified']}"
                )
                if src.get("snippet"):
                    st.caption(f"*…{src['snippet']}…*")
            with cols[1]:
                st.link_button("Open ↗", src["source_url"], use_container_width=True)
            if i < len(sources):
                st.divider()


# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


# ---------------------------------------------------------------------------
# Helper: load / build index (cached across Streamlit reruns)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading knowledge base …")
def get_index_and_engine():
    idx = get_or_build_index(INDEX_DIR)
    eng = build_query_engine(idx)
    return idx, eng


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📂 SharePoint Chatbot")
    st.caption("Powered by LlamaIndex · FAISS · Ollama")
    st.divider()

    st.subheader("⚙️ Settings")
    st.markdown(
        f"""
| Setting | Value |
|---------|-------|
| **Model** | `{OLLAMA_MODEL}` |
| **Endpoint** | `{OLLAMA_BASE_URL}` |
| **Top-K** | `{TOP_K}` |
| **Strict grounded** | `{'Yes' if STRICT_GROUNDED else 'No'}` |
| **Index dir** | `{INDEX_DIR}` |
"""
    )
    st.divider()

    col_rebuild, col_clear = st.columns(2)
    with col_rebuild:
        if st.button("Rebuild Index", use_container_width=True):
            with st.spinner("Rebuilding knowledge base …"):
                try:
                    get_index_and_engine.clear()
                    build_index(INDEX_DIR)
                    st.success("Index rebuilt!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Rebuild failed: {exc}")

    with col_clear:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    st.divider()

    # Document list
    st.subheader("Available Documents")
    try:
        docs = load_mock_documents()
        for doc in docs:
            with st.expander(f"{doc.title}", expanded=False):
                st.markdown(
                    f"**Library:** {doc.library}  \n"
                    f"**Owner:** {doc.owner}  \n"
                    f"**Modified:** {doc.last_modified}  \n"
                    f"[Open in SharePoint]({doc.source_url})"
                )
    except Exception:
        st.warning("Could not load document list.")


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("Contoso SharePoint Chatbot")
st.caption(
    "Ask questions about company policies, procedures, reports, and documents. "
    "Answers are grounded in your SharePoint content."
)

# ---------------------------------------------------------------------------
# Initialise index (once per session; uses Streamlit cache)
# ---------------------------------------------------------------------------
try:
    _index, _engine = get_index_and_engine()
except Exception as exc:
    st.error(
        f"**Failed to initialise the knowledge base.**\n\n"
        f"```\n{exc}\n```\n\n"
        "Make sure the Ollama service is running and the model is available."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Render existing chat history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            render_sources(msg["sources"])

# ---------------------------------------------------------------------------
# New user message
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask anything about Contoso documents ..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Searching documents and generating answer ..."):
            try:
                result = rag_query(_engine, prompt)
                answer = result.answer
                sources_data = [
                    {
                        "title": s.title,
                        "library": s.library,
                        "owner": s.owner,
                        "last_modified": s.last_modified,
                        "source_url": s.source_url,
                        "doc_id": s.doc_id,
                        "snippet": s.snippet,
                    }
                    for s in result.sources
                ]
            except Exception as exc:
                logger.exception("Query failed")
                answer = (
                    f"An error occurred while processing your question:\n\n"
                    f"```\n{exc}\n```\n\n"
                    "Please check that the Ollama service is running and the model is loaded."
                )
                sources_data = []

        st.markdown(answer)
        render_sources(sources_data)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources_data}
    )
