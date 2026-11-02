[![NTI Verified](https://img.shields.io/badge/NTI_Score-82%2F100-brightgreen)](https://nti-registry.vercel.app)

# NTI Secure FastAPI Template

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready FastAPI backend serving AI agents protected by NTI (Neutral Trust Infrastructure) post-quantum security.

Every tool call is cryptographically verified before execution using all 5 pillars of NTI:
1. Zero-Trust Capability Enforcement
2. NIST Post-Quantum Cryptography (Dilithium5 / Kyber1024)
3. BFT Multi-Agent Consensus
4. Merkle-Chained Audit Trails
5. P2P Agent Mesh & State Persistence

## Quick Start

```bash
git clone https://github.com/abisheakp197/nti-fastapi-template.git my-backend
cd my-backend
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
python main.py
```

The server starts at `http://localhost:8000`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Health check |
| POST | /agent/invoke | Invoke the NTI-secured agent |

### Example Request (Health Check)

```bash
curl -i http://localhost:8000/health
```

### Example Request (Agent Invoke - Unsigned, Rejected by NTI)

```bash
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": "Transfer $100 USD to account 12345", "agent_id": "user_001"}'
```

Response:
```json
{"detail": "Missing required NTI cryptographic signature header (X-NTI-Signature)"}
```

### Example Request (Agent Invoke - Signed)

```bash
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -H "X-NTI-Signature: sample_pqc_signature" \
  -d '{"input": "Transfer $100 USD to account 12345", "agent_id": "user_001"}'
```

### Example Response (Success)

```json
{"output": "Transferred 100.0 USD to account 12345", "agent_id": "user_001", "status": "success"}
```

### Example Response (Blocked by NTI Capability Enforcement)

```json
{"detail": "NTI blocked action: NTI Security Denied Action: capability not granted"}
```

## What NTI Does Here

- Intercepts requests and enforces post-quantum cryptographic signatures (`X-NTI-Signature`).
- Only tools with an explicit grant in `agent.py` can be called.
- All evaluations are logged to a Merkle-chained audit trail.
- Unauthorized or missing signature actions return HTTP 401 / 403 before execution.
- Cryptographically signs outgoing HTTP responses (`X-NTI-Response-Signature`).

## How To Add Capabilities

In `agent.py`, add a grant for any tool the agent should be allowed to call:

```python
nti_handler.grant_capability("execute_transfer")
nti_handler.grant_capability("read_account")
```

Any tool without an explicit grant is automatically blocked.

## License

MIT License. See [LICENSE](LICENSE).

## Links

- Core SDK: https://pypi.org/project/ube-foundation/
- LangChain wrapper: https://pypi.org/project/langchain-nti/
- Homepage: https://abisheakp197.github.io/Neutral-Trust-Infrastructure/

## Architecture

```mermaid
graph TD
    subgraph Client ["Client Layer"]
        C1["HTTP Client / AI Agent Consumer"]
        C2["HTTP Request<br/>(Path, Body, X-NTI-Signature)"]
        C3["HTTP Response<br/>(Body + X-NTI-Response-Signature)"]
    end

    subgraph FastAPIApp ["FastAPI App"]
        F1["FastAPI Application"]
        F2["CORS Middleware"]
        F3["GET /health"]
        F4["POST /agent/invoke"]
        F5["LangChain Agent (build_agent)"]
    end

    subgraph NTISecurity ["NTI Security Layer"]
        M1["nti_security_middleware"]
        M2{"Target Path starts with /agent/?"}
        M3["Extract X-NTI-Signature Header"]
        M4{"Header Present?"}
        M5["401 Unauthorized<br/>(Missing NTI Signature Header)"]
        M6["NTICallbackHandler<br/>Capability Verification"]
        M7["403 Forbidden<br/>(Capability Denied)"]
        M8["Response Signer<br/>(path:status_code)"]
    end

    subgraph CryptoEngine ["Crypto Engine (ube-foundation)"]
        K1["PqcKeyPair (Dilithium5 / Kyber1024)"]
        K2["server_pqc_key"]
    end

    %% Flow connections
    C1 -->|"Sends HTTP Request"| C2
    C2 -->|"Intercepted by"| F1
    F1 --> F2
    F2 --> M1

    M1 --> M2
    M2 -->|"No (e.g., /health)"| F3
    M2 -->|"Yes (/agent/*)"| M3

    M3 --> M4
    M4 -->|"No (Unsigned / Missing)"| M5
    M5 -->|"Fail-Closed Rejection"| C3

    M4 -->|"Yes (Signed)"| F4
    F4 --> F5
    F5 --> M6

    M6 -->|"Capability Not Granted"| M7
    M7 -->|"Access Blocked"| C3

    M6 -->|"Capability Allowed"| K1
    K1 -->|"Execute Tool"| F5

    F3 --> M8
    F5 -->|"Return Result"| M8

    M8 -->|"Sign with"| K2
    K2 -->|"Attach X-NTI-Response-Signature & X-NTI-Public-Key"| M8
    M8 -->|"Return Response"| C3
    C3 --> C1
```
