from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DocumentResponse(BaseModel):
    id: str
    title: str
    file_path: str
    category: Optional[str] = None
    file_type: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True

class RAGQueryRequest(BaseModel):
    query_text: str = Field(..., description="The search query or question from the employee")

class ReferenceItem(BaseModel):
    document_title: str = Field(..., description="Title of the source document")
    file_path: str = Field(..., description="Link or storage path to the source document")
    matched_text: str = Field(..., description="Relevant text excerpt extracted from the document")

class RAGQueryResponse(BaseModel):
    answer_text: str = Field(..., description="Contextually synthesized response from the AI")
    references: List[ReferenceItem] = Field(..., description="List of source document snippets used for retrieval")
