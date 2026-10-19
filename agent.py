"""
AI agent with NTI post-quantum security for the FastAPI backend.
"""

from typing import Any

import ube_foundation  # type: ignore[import-untyped]

try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent  # type: ignore[attr-defined]
except (ImportError, AttributeError):
    from langchain_classic.agents import AgentExecutor, create_openai_tools_agent

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_nti import NTICallbackHandler  # type: ignore[import-untyped]
from langchain_openai import ChatOpenAI

# Ensure compatibility with langchain-nti's call to PqcKeyPair.generate()
if not hasattr(ube_foundation.PqcKeyPair, "generate"):
    ube_foundation.PqcKeyPair.generate = classmethod(lambda cls: cls())


@tool
def execute_transfer(amount: float, currency: str, recipient: str) -> str:
    """Execute a financial transfer. Requires NTI capability: execute_transfer."""
    return f"Transferred {amount} {currency} to {recipient}"


@tool
def read_account(account_id: str) -> str:
    """Read account details. Requires NTI capability: read_account."""
    return f"Account {account_id} has balance $5,000"


def build_agent(agent_id: str = "default_agent") -> AgentExecutor:
    """Build an NTI-secured LangChain agent for FastAPI use."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    tools: list[Any] = [execute_transfer, read_account]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful banking assistant."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    agent = create_openai_tools_agent(llm, tools, prompt)

    nti_handler = NTICallbackHandler(agent_id=agent_id)
    nti_handler.grant_capability("execute_transfer")
    nti_handler.grant_capability("read_account")

    return AgentExecutor(
        agent=agent,
        tools=tools,
        callbacks=[nti_handler],
        verbose=False,
    )
