from openai import OpenAI
from .config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def embed_texts(texts: list[str]) -> list[list[float]]:
    # Batch embeddings (sync SDK; acceptable for service worker)
    resp = client.embeddings.create(model=settings.EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]