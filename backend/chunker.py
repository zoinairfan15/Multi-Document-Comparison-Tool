def chunk_text(text: str, paper_id: str, paper_title: str,
                chunk_size: int = 500, overlap: int = 50):
    """Split text into overlapping word chunks, tagged with source paper."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text_str = " ".join(chunk_words)
        chunks.append({
            "text": chunk_text_str,
            "paper_id": paper_id,
            "paper_title": paper_title
        })
        start += chunk_size - overlap
    return chunks