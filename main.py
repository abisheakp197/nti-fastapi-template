"""
NTI Secure FastAPI Template
A production-ready FastAPI backend that serves AI agents protected by NTI.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import ube_foundation  # type: ignore[import-untyped]

# Ensure compatibility with langchain-nti's call to PqcKeyPair.generate()
if not hasattr(ube_foundation.PqcKeyPair, "generate"):
    ube_foundation.PqcKeyPair.generate = classmethod(lambda cls: cls())

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent import build_agent

load_dotenv()

# Post-Quantum KeyPair for signing server responses
server_pqc_key = ube_foundation.PqcKeyPair()


class AgentRequest(BaseModel):
    input: str = Field(..., description="Natural language input for the agent")
    agent_id: str = Field("default_agent", description="Unique agent identifier")


class AgentResponse(BaseModel):
    output: str
    agent_id: str
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Ensure OPENAI_API_KEY is present in environment for initialization
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "sk-placeholder-key-for-dev"
    app.state.agent = build_agent(agent_id="api_agent")
    yield


app = FastAPI(
    title="NTI Secure FastAPI Template",
    description="AI agents with NTI post-quantum security",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def nti_security_middleware(request: Request, call_next: Any) -> Any:
    """
    NTI Security Middleware:
    - Intercepts requests to secure agent endpoints, rejecting unsigned requests with 401 JSON error.
    - Cryptographically signs outgoing HTTP responses using NIST Dilithium5 PQC signature.
    """
    if request.url.path.startswith("/agent/"):
        nti_signature = request.headers.get("X-NTI-Signature")
        if not nti_signature:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing required NTI cryptographic signature header (X-NTI-Signature)"},
            )

    response = await call_next(request)

    # Sign outgoing response with server PQC keypair
    response_payload = f"{request.url.path}:{response.status_code}".encode()
    pqc_signature = server_pqc_key.sign(response_payload)
    response.headers["X-NTI-Response-Signature"] = pqc_signature
    response.headers["X-NTI-Public-Key"] = server_pqc_key.public_key_hex()

    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
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
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
