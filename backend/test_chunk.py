from pdf_parser import extract_text
from chunker import chunk_text

text = extract_text("papers/2201.00978v1.pdf")
chunks = chunk_text(text, paper_id="2201.00978v1", paper_title="PyramidTNT")

print(f"Total chunks created: {len(chunks)}")
print(f"\n--- First chunk ---\n{chunks[0]['text'][:300]}")
print(f"\n--- Chunk metadata ---\npaper_id: {chunks[0]['paper_id']}, paper_title: {chunks[0]['paper_title']}")