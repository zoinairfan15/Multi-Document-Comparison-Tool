import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
from fastapi import File, UploadFile
from typing import List
import uuid
from arxiv_fetcher import search_arxiv, download_paper
from pdf_parser import extract_text
from chunker import chunk_text
from vector_store import add_chunks, query_per_paper, get_embedding_visualization
from llm_client import compare_papers, check_faithfulness
app = FastAPI()

# Allow the React frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # default Vite dev server port
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent store of processed papers: {paper_id: title}
PAPERS_STORE_FILE = "processed_papers.json"

def load_processed_papers():
    if os.path.exists(PAPERS_STORE_FILE):
        with open(PAPERS_STORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_processed_papers():
    with open(PAPERS_STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(processed_papers, f, indent=2)

processed_papers = load_processed_papers()


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class IngestRequest(BaseModel):
    paper_ids: list[str]  # ids from the search results the user wants to ingest
    papers_meta: dict      # {paper_id: {title, pdf_url}}


class CompareRequest(BaseModel):
    query: str
    paper_ids: list[str]

class VisualizeRequest(BaseModel):
    paper_ids: list[str]    


@app.get("/")
def root():
    return {"status": "running"}


@app.post("/search")
def search(req: SearchRequest):
    """Search arXiv, return paper metadata (no download yet)."""
    results = search_arxiv(req.query, req.max_results)
    return {"papers": results}


@app.post("/ingest")
def ingest(req: IngestRequest):
    """Download, parse, chunk, and embed the selected papers."""
    for pid in req.paper_ids:
        meta = req.papers_meta[pid]
        path = download_paper(meta["pdf_url"], pid)
        text = extract_text(path)
        chunks = chunk_text(text, pid, meta["title"])
        add_chunks(chunks)
        processed_papers[pid] = meta["title"]
        save_processed_papers()
        return {"status": "ingested", "paper_ids": req.paper_ids}


@app.post("/compare")
def compare(req: CompareRequest):
    """Run the comparison query across selected, already-ingested papers, with evaluation metrics."""
    titles = {pid: processed_papers.get(pid, pid) for pid in req.paper_ids}

    t0 = time.time()
    retrieved, scores = query_per_paper(req.query, req.paper_ids, k=3)
    retrieval_time = round(time.time() - t0, 2)

    t1 = time.time()
    answer = compare_papers(req.query, retrieved, titles)
    generation_time = round(time.time() - t1, 2)

    faithfulness = check_faithfulness(answer, retrieved)

    # Extract a simple faithfulness rating from the text (High/Medium/Low)
    rating = "Unknown"
    for level in ["High", "Medium", "Low"]:
        if level in faithfulness:
            rating = level
            break

    # Average relevance score across all retrieved chunks, all papers
    all_scores = [s for paper_scores in scores.values() for s in paper_scores]
    avg_relevance = round(sum(all_scores) / len(all_scores), 3) if all_scores else 0

    return {
        "answer": answer,
        "faithfulness": faithfulness,
        "sources": retrieved,
        "titles": titles,
        "metrics": {
            "retrieval_time_sec": retrieval_time,
            "generation_time_sec": generation_time,
            "avg_relevance_score": avg_relevance,
            "faithfulness_rating": rating,
            "chunks_retrieved": len(all_scores),
        }
    }

@app.post("/visualize")
def visualize(req: VisualizeRequest):
    """Return 2D coordinates of chunk embeddings for the given papers, for plotting."""
    return get_embedding_visualization(req.paper_ids)


@app.post("/upload")
async def upload_and_ingest(files: List[UploadFile] = File(...)):
    """Accept user-uploaded PDFs, parse/chunk/embed them immediately."""
    ingested = []
    save_dir = "papers"
    os.makedirs(save_dir, exist_ok=True)

    for file in files:
        paper_id = str(uuid.uuid4())[:8]
        title = file.filename.replace(".pdf", "")
        path = os.path.join(save_dir, f"{paper_id}.pdf")

        content = await file.read()
        with open(path, "wb") as f:
            f.write(content)

        text = extract_text(path)
        chunks = chunk_text(text, paper_id, title)
        add_chunks(chunks)
        processed_papers[paper_id] = title
        ingested.append({"id": paper_id, "title": title})

    save_processed_papers()
    return {"status": "ingested", "papers": ingested}
