import os
from pdf_parser import extract_text
from chunker import chunk_text
from vector_store import add_chunks, query_per_paper
from llm_client import compare_papers

papers_dir = "papers"
paper_titles = {
    "2201.00978v1": "PyramidTNT",
    "2305.11403v5": "Pre-RMSNorm and Pre-CRMSNorm Transformers",
    "2305.14858v2": "Efficient Mixed Transformer for Single Image Super-Resolution"
}

paper_ids = list(paper_titles.keys())

query = "What architecture or method do they propose?"
retrieved = query_per_paper(query, paper_ids, k=3)

answer = compare_papers(query, retrieved, paper_titles)
print(answer)