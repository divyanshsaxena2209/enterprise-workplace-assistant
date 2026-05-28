def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Splits text into smaller chunks for vector embedding.
    Uses a simple word-based splitting strategy with overlap.
    """
    words = text.split()
    chunks = []
    
    if not words:
        return chunks
        
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        # Advance by chunk_size - overlap to ensure context preservation
        start += (chunk_size - overlap)
        
    return chunks
