import arxiv
import os
import requests

def search_arxiv(query: str, max_results: int = 5):
    """Search arXiv and return paper metadata."""
    client = arxiv.Client(
        page_size=max_results,
        delay_seconds=1,
        num_retries=1,  # fail fast instead of retrying for minutes
    )
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    try:
        results = []
        for paper in client.results(search):
            results.append({
                "id": paper.entry_id.split("/")[-1],
                "title": paper.title,
                "authors": [a.name for a in paper.authors],
                "summary": paper.summary,
                "pdf_url": paper.pdf_url
            })
        return results
    except Exception as e:
        raise Exception(f"arXiv search failed (possibly rate-limited): {e}")

def download_paper(pdf_url: str, paper_id: str, save_dir: str = "papers"):
    """Download a paper PDF locally using requests (more reliable SSL handling on Windows)."""
    os.makedirs(save_dir, exist_ok=True)
    path = os.path.join(save_dir, f"{paper_id}.pdf")
    if not os.path.exists(path):
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)
    return path