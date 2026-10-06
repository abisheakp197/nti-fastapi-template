"""
NTI Secure FastAPI Template
A production-ready FastAPI backend that serves AI agents protected by NTI.
"""

import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent import build_agent

load_dotenv()


class AgentRequest(BaseModel):
    input: str = Field(..., description="Natural language input for the agent")
    agent_id: str = Field("default_agent", description="Unique agent identifier")


class AgentResponse(BaseModel):
    output: str
    agent_id: str
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = build_agent(agent_id="api_agent")
    yield


app = FastAPI(
    title="NTI Secure FastAPI Template",
    description="AI agents with NTI post-quantum security",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "healthy", "service": "nti-fastapi-template"}


@app.post("/agent/invoke", response_model=AgentResponse)
async def invoke_agent(request: AgentRequest) -> AgentResponse:
    try:
        result = app.state.agent.invoke({"input": request.input})
        return AgentResponse(
            output=result["output"],
            agent_id=request.agent_id,
            status="success",
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=f"NTI blocked action: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
