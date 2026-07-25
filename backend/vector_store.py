import chromadb
import gc
from sentence_transformers import SentenceTransformer


model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("papers")

def add_chunks(chunks: list, batch_size: int = 8):
    """Embed and store chunks with metadata, in small batches to limit peak memory."""
    texts = [c["text"] for c in chunks]
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch).tolist()
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
    query_embedding = model.encode([query]).tolist()
    results = {}
    scores = {}
    for pid in paper_ids:
        res = collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            where={"paper_id": pid}
        )
        results[pid] = res["documents"][0] if res["documents"] else []
        # ChromaDB returns distances (lower = more similar); convert to a 0-1 relevance score
        distances = res["distances"][0] if res["distances"] else []
        scores[pid] = [round(1 - d, 3) for d in distances] if distances else []
    return results, scores
from sklearn.decomposition import PCA

def get_embedding_visualization(paper_ids: list):
    """Fetch all chunk embeddings for the given papers and reduce to 2D for plotting."""
    all_embeddings = []
    all_labels = []
    all_texts = []

    for pid in paper_ids:
        res = collection.get(
            where={"paper_id": pid},
            include=["embeddings", "documents"]
        )
        if res["embeddings"] is not None and len(res["embeddings"]) > 0:
            all_embeddings.extend(res["embeddings"])
            all_labels.extend([pid] * len(res["embeddings"]))
            all_texts.extend([doc[:80] for doc in res["documents"]])

    if len(all_embeddings) < 2:
        return {"points": []}

    pca = PCA(n_components=2)
    coords = pca.fit_transform(all_embeddings)

    points = [
        {"x": round(float(coords[i][0]), 3), "y": round(float(coords[i][1]), 3),
         "paper_id": all_labels[i], "preview": all_texts[i]}
        for i in range(len(coords))
    ]
    return {"points": points}