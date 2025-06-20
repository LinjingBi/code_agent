from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uvicorn
from typing import List, Dict

from agent.agent import CodeAgent, CodeAgentResponse
from agent.manager import ManagerAgent
from agent.jupyter_agent import JupyterCodeAgent
from agent.jupyter_kernel import get_kernel, JupyterKernelManager

app = FastAPI(
    title="Code Agent API",
    description="An AI-powered coding assistant API",
    version="1.0.0"
)

# Initialize the code agents
code_agent = CodeAgent()
manager_agent = ManagerAgent()
# jupyter_agent = JupyterCodeAgent()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "Code Agent API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # TODO - return summarized message, not derive progress from code agent
        code_response = await code_agent.answer_question(
            question=request.message
        )
        mgr_resp = await manager_agent.summary(
            code_response
        )
        return ChatResponse(
            response=mgr_resp,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/chat-jupyter", response_model=ChatResponse)
# async def chat_jupyter(
#     request: ChatRequest,
#     kernel_manager: JupyterKernelManager = Depends(get_kernel)
# ):
#     try:
#         response = jupyter_agent.answer_question(
#             message=request.message,
#             kernel_manager=kernel_manager
#         )
#         return ChatResponse(
#             response=response,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
