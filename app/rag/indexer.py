"""
RAG indexer: builds and persists a FAISS vector index using LlamaIndex.

Embeddings are generated locally with sentence-transformers (all-MiniLM-L6-v2)
to keep costs at zero.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from llama_index.core import (
    Settings,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.schema import Document as LlamaDocument
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore

import faiss

from app.connectors.mock_connector import SharePointDocument, load_mock_documents

logger = logging.getLogger(__name__)

_EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_EMBED_DIM = 384  # all-MiniLM-L6-v2 output dimension


def _get_embed_model() -> HuggingFaceEmbedding:
    return HuggingFaceEmbedding(model_name=_EMBED_MODEL_NAME)


def _sp_docs_to_llama(docs: List[SharePointDocument]) -> List[LlamaDocument]:
    """Convert SharePointDocument objects to LlamaIndex Document objects."""
    llama_docs: List[LlamaDocument] = []
    for doc in docs:
        llama_docs.append(
            LlamaDocument(
                text=doc.content,
                metadata=doc.metadata_dict(),
                doc_id=doc.doc_id,
            )
        )
    return llama_docs


def build_index(index_dir: str | None = None) -> VectorStoreIndex:
    """Build a fresh FAISS index and persist it to *index_dir*."""
    index_dir = _resolve_index_dir(index_dir)
    logger.info("Building FAISS index → %s", index_dir)

    embed_model = _get_embed_model()
    Settings.embed_model = embed_model
    Settings.llm = None  # LLM is injected at query time via Ollama

    data_dir = os.environ.get("DATA_DIR", None)
    sp_docs = load_mock_documents(data_dir)
    if not sp_docs:
        raise RuntimeError("No documents found. Check DATA_DIR environment variable.")
    llama_docs = _sp_docs_to_llama(sp_docs)

    faiss_index = faiss.IndexFlatL2(_EMBED_DIM)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_ctx = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_documents(
        llama_docs,
        storage_context=storage_ctx,
        show_progress=True,
    )

    Path(index_dir).mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=index_dir)
    logger.info("Index persisted to %s", index_dir)
    return index


def load_index(index_dir: str | None = None) -> VectorStoreIndex:
    """Load an existing FAISS index from *index_dir*."""
    index_dir = _resolve_index_dir(index_dir)
    logger.info("Loading FAISS index from %s", index_dir)

    embed_model = _get_embed_model()
    Settings.embed_model = embed_model
    Settings.llm = None

    vector_store = FaissVectorStore.from_persist_dir(index_dir)
    storage_ctx = StorageContext.from_defaults(
        vector_store=vector_store, persist_dir=index_dir
    )
    index = load_index_from_storage(storage_ctx)
    return index


def get_or_build_index(index_dir: str | None = None) -> VectorStoreIndex:
    """Load the existing index if present; otherwise build a new one."""
    index_dir = _resolve_index_dir(index_dir)
    docstore_path = Path(index_dir) / "docstore.json"
    if docstore_path.exists():
        try:
            return load_index(index_dir)
        except Exception as exc:
            logger.warning("Failed to load existing index (%s). Rebuilding.", exc)
    return build_index(index_dir)


def _resolve_index_dir(index_dir: str | None) -> str:
    if index_dir:
        return index_dir
    return os.environ.get("INDEX_DIR", "/app/.index")
