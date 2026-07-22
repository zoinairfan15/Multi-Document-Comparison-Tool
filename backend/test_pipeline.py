import os
from pdf_parser import extract_text
from chunker import chunk_text
from vector_store import add_chunks, query_per_paper

papers_dir = "papers"
paper_titles = {
    "2201.00978v1": "PyramidTNT",
    "2305.11403v5": "Pre-RMSNorm and Pre-CRMSNorm Transformers",
    "2305.14858v2": "Efficient Mixed Transformer for Single Image Super-Resolution"
}

paper_ids = []
for filename in os.listdir(papers_dir):
    if filename.endswith(".pdf"):
        paper_id = filename.replace(".pdf", "")
        title = paper_titles.get(paper_id, paper_id)
        path = os.path.join(papers_dir, filename)

        text = extract_text(path)
        chunks = chunk_text(text, paper_id, title)
        add_chunks(chunks)
        paper_ids.append(paper_id)
        print(f"Processed {title}: {len(chunks)} chunks")

print("\n--- Querying across all papers ---")
results = query_per_paper("What method or architecture do they propose?", paper_ids)
for pid, chunks in results.items():
    print(f"\n--- {pid} ---")
    if chunks:
        print(chunks[0][:200])
    else:
        print("No results found")