# Multi-Document Comparison Tool

A Generative AI tool that compares multiple research papers (or any user-uploaded PDFs) using Retrieval-Augmented Generation (RAG). Search arXiv or upload your own documents, select what to compare, and ask questions that get answered with a structured, citation-grounded comparison — agreements, differences, and each paper's unique contributions — backed by an automated faithfulness check and inspectable source chunks.

## Why this project

Most RAG demos answer questions about a single document. This tool instead retrieves fairly across *multiple* documents at once and forces the LLM to reason comparatively, with citations back to the specific document each claim came from — and lets the user directly verify those claims against the retrieved source text, rather than trusting the LLM's word alone.

## Features

- **Two ways to get documents in**: search arXiv directly, or upload your own PDFs — the two can even be mixed in a single comparison
- **Fair, per-document retrieval**: top-k chunks are retrieved *per document*, not globally, so no single long/dense document dominates the comparison
- **Structured comparison**: every answer is broken into Agreements, Disagreements/Differences, and Unique Contributions, with claims attributed to specific documents
- **Faithfulness check**: a second LLM call cross-verifies the generated comparison against the retrieved context and flags unsupported claims
- **Click-to-source citations**: expand any document's retrieved chunks to manually verify a claim against the original source text
- **Evaluation metrics panel**: retrieval relevance score, retrieval/generation latency, faithfulness rating, and chunk count — shown for every query, not just claimed in a report
- **Embedding visualization**: a 2D PCA projection of chunk embeddings, color-coded per document, visually demonstrating why per-document retrieval matters
- **Downloadable reports**: export any comparison (with faithfulness check and metrics) as a Markdown file
- **Persistent metadata**: processed document titles survive server restarts (written to disk, not just kept in memory)

## Architecture

**Backend (FastAPI + Python)**
- `arxiv_fetcher.py` — searches and downloads papers from the arXiv API
- `pdf_parser.py` — extracts text with PyMuPDF, trims reference/bibliography sections before chunking
- `chunker.py` — splits text into overlapping chunks, tagged with source document metadata
- `vector_store.py` — embeds chunks (`sentence-transformers`) and stores them in ChromaDB; retrieves top-k chunks **per document** (not globally); also computes a 2D PCA projection of embeddings for visualization
- `llm_client.py` — builds the comparison prompt (Groq / Llama 3.3) and runs a second LLM call to verify the answer is supported by the retrieved context
- `main.py` — exposes `/search`, `/upload`, `/ingest`, `/compare`, `/visualize` endpoints; persists processed-document metadata to disk

**Frontend (React + Vite)**
- Search arXiv or upload PDFs → select documents → ask a question → view structured comparison, faithfulness report, evaluation metrics, source chunks, and embedding plot → download as a report

## Tech stack

| Layer | Tool |
|---|---|
| LLM | Groq API (Llama 3.3 70B) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Dimensionality reduction | scikit-learn (PCA) |
| Vector DB | ChromaDB |
| PDF parsing | PyMuPDF |
| Backend | FastAPI |
| Frontend | React + Vite, Axios |
| Data sources | arXiv API, user file upload |

## Key design decisions

- **Per-document retrieval, not global top-k.** A naive RAG setup retrieves the globally most similar chunks, which lets one long or dense document dominate. This tool retrieves top-k chunks *per selected document*, so every document gets a fair say in the comparison.
- **Reference-section trimming.** Bibliography text (author lists, years) was polluting embeddings and retrieval; the parser detects and trims the document before the References/Bibliography heading.
- **Faithfulness as a first-class, inspectable feature**, not an afterthought. Beyond an automated LLM-based faithfulness rating, users can expand the exact retrieved chunks behind any claim — directly addressing RAG's most common failure mode (hallucination) with both an automated check and manual verifiability.
- **Measured, not just built.** Every comparison reports retrieval relevance, latency, and faithfulness rating, rather than treating RAG quality as unmeasured.

## Running locally

**Backend**
```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
uvicorn main:app
```
Create a `.env` file in `backend/` with:
GROQ_API_KEY=your_key_here


**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`.

## Example query

> "What method or architecture do they propose?"

Returns a structured breakdown of agreements, differences, and unique contributions across the selected documents, each claim attributed to its source, followed by a faithfulness rating, evaluation metrics, and an option to inspect source chunks or download the full report.

## Possible extensions

- Support `.docx` and `.txt` uploads, not just PDF
- Multi-turn follow-up questions instead of one-shot comparisons
- Docker containerization for easier deployment
- Swap Groq for a locally-run LLM (e.g. via Ollama) for a fully offline mode