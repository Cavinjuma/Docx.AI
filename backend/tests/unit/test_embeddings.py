from app.embeddings import HashingEmbeddingProvider
from app.retrieval import MemoryVectorStore


def test_hashing_embedding_provider_returns_fixed_length_vector() -> None:
    provider = HashingEmbeddingProvider(dimensions=8)

    vector = provider.embed_text("employee leave policy")

    assert len(vector) == 8
    assert all(isinstance(value, float) for value in vector)


def test_memory_vector_store_returns_most_similar_chunk() -> None:
    provider = HashingEmbeddingProvider(dimensions=8)
    store = MemoryVectorStore(provider)

    store.add("alpha", "dogs bark at night")
    store.add("beta", "cats sleep during the day")

    results = store.search("dogs are loud at night", limit=1)

    assert results[0]["id"] == "alpha"
    assert results[0]["score"] >= results[1]["score"] if len(results) > 1 else True
