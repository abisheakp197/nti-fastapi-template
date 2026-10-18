"""
Tests for NTI Secure FastAPI Template.
"""

from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
import ube_foundation  # type: ignore[import-untyped]
from fastapi.testclient import TestClient

from agent import execute_transfer, read_account
from main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "nti-fastapi-template"}
    assert "X-NTI-Response-Signature" in response.headers
    assert "X-NTI-Public-Key" in response.headers


def test_invoke_agent_missing_signature(client: TestClient) -> None:
    response = client.post(
        "/agent/invoke",
        json={"input": "Hello", "agent_id": "user_001"},
    )
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Missing required NTI cryptographic signature header (X-NTI-Signature)"
    }


def test_invoke_agent_with_signature(client: TestClient) -> None:
    # Mock app.state.agent.invoke to avoid calling OpenAI in unit test
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {"output": "Transferred 100 USD to account 12345"}
    app.state.agent = mock_agent

    kp = ube_foundation.PqcKeyPair()
    sig = kp.sign(b"test-request")

    response = client.post(
        "/agent/invoke",
        headers={"X-NTI-Signature": sig},
        json={"input": "Transfer $100 to 12345", "agent_id": "user_001"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "output": "Transferred 100 USD to account 12345",
        "agent_id": "user_001",
        "status": "success",
    }
    assert "X-NTI-Response-Signature" in response.headers
    assert "X-NTI-Public-Key" in response.headers


def test_agent_permission_error(client: TestClient) -> None:
    mock_agent = MagicMock()
    mock_agent.invoke.side_effect = PermissionError("Capability execute_transfer not granted")
    app.state.agent = mock_agent

    kp = ube_foundation.PqcKeyPair()
    sig = kp.sign(b"test-request")

    response = client.post(
        "/agent/invoke",
        headers={"X-NTI-Signature": sig},
        json={"input": "Transfer $100", "agent_id": "user_001"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "NTI blocked action: Capability execute_transfer not granted"
    }


def test_tools_direct() -> None:
    assert execute_transfer.invoke({"amount": 100.0, "currency": "USD", "recipient": "12345"}) == "Transferred 100.0 USD to 12345"
    assert read_account.invoke({"account_id": "12345"}) == "Account 12345 has balance $5,000"
