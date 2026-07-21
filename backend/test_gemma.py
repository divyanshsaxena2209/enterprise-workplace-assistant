import os
from google import genai
from pydantic import BaseModel
from app.core.config import settings

class MySchema(BaseModel):
    value: str

client = genai.Client(api_key=settings.GEMINI_API_KEY)
print(client.models.generate_content(
    model='gemma-4-31b-it', 
    contents='say hello', 
    config=genai.types.GenerateContentConfig(
        response_mime_type='application/json', 
        response_schema=MySchema
    )
).text)
