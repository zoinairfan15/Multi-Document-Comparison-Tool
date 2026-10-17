
import chromadb
import gc
from fastembed import TextEmbedding

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    "papers", metadata={"hnsw:space": "cosine"}
)

_model = None

def get_embeddings(texts: list, retries: int = 3):
    """Embed text locally with the same MiniLM model (no API needed)."""
    global _model
    if _model is None:
        _model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    return [vec.tolist() for vec in _model.embed(texts)]

def add_chunks(chunks: list, batch_size: int = 8):
    """Embed (via hosted API) and store chunks with metadata, in small batches."""
    texts = [c["text"] for c in chunks]
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = get_embeddings(batch)
        all_embeddings.extend(batch_embeddings)
    embeddings = all_embeddings

    ids = [f"{c['paper_id']}_{i}" for i, c in enumerate(chunks)]
    metadatas = [{"paper_id": c["paper_id"], "paper_title": c["paper_title"]} for c in chunks]

    collection.add(
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )
    gc.collect()


def query_per_paper(query: str, paper_ids: list, k: int = 3):
    """Retrieve top-k chunks PER paper, along with similarity scores for evaluation."""
    query_embedding = get_embeddings([query])
    results = {}
    scores = {}
    for pid in paper_ids:
        res = collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            where={"paper_id": pid}
        )
        results[pid] = res["documents"][0] if res["documents"] else []
        distances = res["distances"][0] if res["distances"] else []
        scores[pid] = [round(1 - d, 3) for d in distances] if distances else []
    return results, scores

