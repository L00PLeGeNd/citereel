from citereel.retrieve.base import Retriever
from citereel.retrieve.embedding import EmbeddingRetriever, default_embedding_retriever
from citereel.retrieve.keyword import KeywordRetriever

__all__ = [
    "EmbeddingRetriever",
    "KeywordRetriever",
    "Retriever",
    "default_embedding_retriever",
]


def build_retriever(name: str = "embedding") -> Retriever:
    key = name.lower().strip()
    if key == "keyword":
        return KeywordRetriever()
    if key == "embedding":
        return default_embedding_retriever()
    raise ValueError(f"unknown retriever {name!r}; use 'embedding' or 'keyword'")
