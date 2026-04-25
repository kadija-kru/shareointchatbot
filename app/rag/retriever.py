"""
RAG query engine: wraps the FAISS index with an Ollama LLM.

Returns both the generated answer and a list of source nodes with
full SharePoint metadata.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.llms.ollama import Ollama

logger = logging.getLogger(__name__)

_GROUNDED_SYSTEM_PROMPT = (
    "You are a helpful SharePoint knowledge assistant for Contoso Corporation. "
    "Answer the user's question using ONLY the information provided in the context below. "
    "If the context does not contain enough information to answer the question, "
    "say: 'I could not find a definitive answer in the available documents. "
    "Please consult the source documents or contact the relevant team.' "
    "Always cite the document titles you used."
)

_OPEN_SYSTEM_PROMPT = (
    "You are a helpful SharePoint knowledge assistant for Contoso Corporation. "
    "Answer the user's question using the context provided. "
    "If you are unsure, say so and suggest consulting the source documents."
)


@dataclass
class SourceInfo:
    title: str
    library: str
    owner: str
    last_modified: str
    source_url: str
    doc_id: str
    snippet: str


@dataclass
class QueryResult:
    answer: str
    sources: List[SourceInfo]


def build_query_engine(index: VectorStoreIndex) -> RetrieverQueryEngine:
    """Create a RetrieverQueryEngine backed by Ollama."""
    ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.1")
    top_k = int(os.environ.get("TOP_K", "4"))
    strict_grounded = os.environ.get("STRICT_GROUNDED", "true").lower() == "true"

    llm = Ollama(
        model=ollama_model,
        base_url=ollama_base_url,
        request_timeout=120.0,
        system_prompt=_GROUNDED_SYSTEM_PROMPT if strict_grounded else _OPEN_SYSTEM_PROMPT,
    )
    Settings.llm = llm

    retriever = VectorIndexRetriever(index=index, similarity_top_k=top_k)
    response_synthesizer = get_response_synthesizer()

    engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
    )
    return engine


def query(engine: RetrieverQueryEngine, question: str) -> QueryResult:
    """Run a RAG query and return the answer with source metadata."""
    response = engine.query(question)

    sources: List[SourceInfo] = []
    seen_ids: set[str] = set()

    for node in response.source_nodes:
        meta = node.node.metadata or {}
        doc_id = meta.get("doc_id", node.node.node_id)
        if doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)

        sources.append(
            SourceInfo(
                title=meta.get("title", "Unknown Document"),
                library=meta.get("library", ""),
                owner=meta.get("owner", ""),
                last_modified=meta.get("last_modified", ""),
                source_url=meta.get("source_url", ""),
                doc_id=doc_id,
                snippet=node.node.get_content()[:300].strip(),
            )
        )

    return QueryResult(answer=str(response), sources=sources)
