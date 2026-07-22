import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def compare_papers(query: str, retrieved_chunks: dict, paper_titles: dict):
    """
    retrieved_chunks: {paper_id: [chunk texts]}
    paper_titles: {paper_id: title}
    """
    context_blocks = []
    for pid, chunks in retrieved_chunks.items():
        title = paper_titles.get(pid, pid)
        combined = "\n".join(chunks)
        context_blocks.append(f"=== Paper: {title} (ID: {pid}) ===\n{combined}")

    context = "\n\n".join(context_blocks)

    prompt = f"""You are analyzing multiple research papers to answer a comparison question.

Question: {query}

Below is relevant context extracted from each paper:

{context}

Based ONLY on the context above, provide a structured comparison with these sections:
1. **Agreements** - where papers align or use similar approaches
2. **Disagreements/Differences** - where papers differ in approach or findings
3. **Unique Contributions** - what each paper uniquely contributes

For every claim, cite which paper it came from by title. If the context doesn't contain enough information to answer, say so clearly.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content
def check_faithfulness(answer: str, retrieved_chunks: dict) -> str:
    """
    Verify whether claims in the answer are supported by the retrieved context.
    Returns a short faithfulness report.
    """
    all_context = "\n\n".join(
        "\n".join(chunks) for chunks in retrieved_chunks.values()
    )

    prompt = f"""You are a fact-checker. Below is a generated answer and the source context it was supposed to be based on.

SOURCE CONTEXT:
{all_context}

GENERATED ANSWER:
{answer}

Check whether the claims in the GENERATED ANSWER are supported by the SOURCE CONTEXT.
Respond in this exact format:
- Faithfulness: [High / Medium / Low]
- Unsupported claims (if any): [list them briefly, or write "None found"]
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return response.choices[0].message.content