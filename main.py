from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from agent.agent import CodeAgent
from utils.config import settings

app = FastAPI(
    title="Code Agent API",
    description="An AI-powered coding assistant API",
    version="1.0.0"
)

# Initialize the code agent with system prompt from config
agent = CodeAgent(system_prompt=settings.system_prompt)

class ChatRequest(BaseModel):
    message: str
    context: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "Code Agent API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = agent.process_message(
            message=request.message,
            context=request.context
        )
        return ChatResponse(
            response=response,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
