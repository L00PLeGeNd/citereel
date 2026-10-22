"""citereel: verifiable, comparable, reproducible RAG run records."""

from citereel.generate import Generator, OfflineGenerator
from citereel.html import render_html
from citereel.ingest import load_docs
from citereel.models import Chunk, Citation, Run, Step
from citereel.pipeline import ask
from citereel.retrieve import EmbeddingRetriever, KeywordRetriever, Retriever, build_retriever
from citereel.version import __version__

__all__ = [
    "Chunk",
    "Citation",
    "EmbeddingRetriever",
    "Generator",
    "KeywordRetriever",
    "OfflineGenerator",
    "Retriever",
    "Run",
    "Step",
    "ask",
    "build_retriever",
    "load_docs",
    "render_html",
    "__version__",
]
