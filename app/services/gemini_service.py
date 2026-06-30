from google import genai
from google.genai import types
from app.config import settings

# Initialize client if API key is provided
client = None
if settings.GEMINI_API_KEY:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
else:
    # Print a warning but don't crash server startup so health checks still pass
    print("WARNING: GEMINI_API_KEY is not configured in .env. Gemini operations will fail.")

def get_embedding(text: str) -> list[float]:
    """
    Generates a 768-dimension vector embedding for the input text using text-embedding-004.
    """
    if not client:
        raise ValueError("Gemini Client is not initialized. Please set GEMINI_API_KEY in your .env file.")
    
    response = client.models.embed_content(
        model="text-embedding-004",
        contents=text
    )
    return response.embeddings[0].values

def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generates vector embeddings for a list of text strings in a single batch request.
    Useful for historical backfills to reduce API overhead.
    """
    if not client:
        raise ValueError("Gemini Client is not initialized. Please set GEMINI_API_KEY in your .env file.")
    if not texts:
        return []
    
    response = client.models.embed_content(
        model="text-embedding-004",
        contents=texts
    )
    return [emb.values for emb in response.embeddings]
