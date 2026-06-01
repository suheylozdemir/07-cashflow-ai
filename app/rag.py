import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

INDEX_NAME = "cashflow-ai-gst"

ATO_URLS = [
    "https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst",
    "https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/how-gst-works",
    "https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/your-industry/gst-and-food/gst-free-food",
    "https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/your-industry/gst-and-food/taxable-food",
    "https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/your-industry/gst-and-food/gst-food-classification-guidance",
    "https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/when-to-charge-gst-and-when-not-to",
    "https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/when-to-charge-gst-and-when-not-to/gst-free-sales",
    "https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/when-to-charge-gst-and-when-not-to/taxable-sales",
    "https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/claiming-gst-credits",
    "https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/business-activity-statements-bas/goods-and-services-tax-gst/simpler-bas-gst-bookkeeping-guide",
]

def get_pinecone_index():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    existing = [i.name for i in pc.list_indexes()]
    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(INDEX_NAME)

def get_embedding(text: str) -> list:
    client = OpenAI()
    response = client.embeddings.create(
        input=text[:8000],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def fetch_ato_content(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:10000]
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def index_ato_documents():
    index = get_pinecone_index()
    total_chunks = 0

    for url in ATO_URLS:
        print(f"Fetching: {url}")
        content = fetch_ato_content(url)
        if not content:
            continue

        chunks = chunk_text(content)
        vectors = []

        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            vectors.append({
                "id": f"ato_{hash(url)}_{i}",
                "values": embedding,
                "metadata": {
                    "source": url,
                    "content": chunk
                }
            })

        index.upsert(vectors=vectors)
        total_chunks += len(chunks)
        print(f"  Indexed {len(chunks)} chunks")

    print(f"\nTotal indexed: {total_chunks} chunks from {len(ATO_URLS)} ATO pages")
    return total_chunks

def query_gst_rules(question: str, top_k: int = 3) -> str:
    index = get_pinecone_index()
    embedding = get_embedding(question)

    results = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )

    if not results["matches"]:
        return "No relevant GST information found."

    context = "\n\n".join([
        f"Source: {m['metadata']['source']}\n{m['metadata']['content']}"
        for m in results["matches"]
    ])

    return context