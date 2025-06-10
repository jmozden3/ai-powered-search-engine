from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn

# Import your search engine module (assuming you save the previous code as search_engine.py)
from document_rag import process_question

app = FastAPI(
    title="Legal Search Engine API",
    description="API for searching legal enforcement documents and generating answers",
    version="1.0.0"
)

# Request model
class ChatRequest(BaseModel):
    question: str

# Response models
class Document(BaseModel):
    id: str
    content: str
    title: str
    browser_file: str
    date_issued: str
    document_types: str
    settlement_amount: Any
    sanction_programs: str
    industries: str
    score: float

class ChatResponse(BaseModel):
    question: str
    documents: List[Document]
    answer: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Legal Search Engine API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint that processes user questions and returns search results with AI-generated answers.
    
    Args:
        request: ChatRequest containing the user's question
        
    Returns:
        ChatResponse containing the question, relevant documents, and AI-generated answer
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Call the process_question function from your search engine
        result = process_question(request.question)
        
        # Convert to response model
        response = ChatResponse(
            question=result["question"],
            documents=[Document(**doc) for doc in result["documents"]],
            answer=result["answer"]
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "Legal Search Engine API"}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )