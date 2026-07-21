from google import genai
from app.core.config import settings

genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

def generate_embeddings(texts: list[str], model: str = "text-embedding-004") -> list[list[float]]:
    """Generate vector embeddings for a list of text chunks."""
    if not texts:
        return []
        
    # Replace newlines with spaces as recommended for better embeddings
    cleaned_texts = [text.replace("\n", " ") for text in texts]
    
    response = genai_client.models.embed_content(
        model=model,
        contents=cleaned_texts
    )
    
    # Gemini embed_content returns a list of embeddings directly if inputs is a list
    return [e.values for e in response.embeddings]

def generate_embedding(text: str, model: str = "text-embedding-004") -> list[float]:
    """Generate a single vector embedding."""
    response = genai_client.models.embed_content(
        model=model,
        contents=text
    )
    return response.embeddings[0].values
