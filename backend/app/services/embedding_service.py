from openai import OpenAI
from app.core.config import settings

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_embeddings(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    """Generate vector embeddings for a list of text chunks."""
    if not texts:
        return []
        
    # Replace newlines with spaces as recommended by OpenAI for better embeddings
    cleaned_texts = [text.replace("\n", " ") for text in texts]
    
    response = openai_client.embeddings.create(
        input=cleaned_texts,
        model=model
    )
    
    return [data.embedding for data in response.data]

def generate_embedding(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """Generate a single vector embedding."""
    return generate_embeddings([text], model)[0]
