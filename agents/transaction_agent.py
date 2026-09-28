import json
from pathlib import Path
from typing import Any

from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage
from model import model
from schemas import TransactionResult, parse_llm_json
from state import ExpenseState
from tools.tool import filter_transactions, load_transactions

TRANSACTION_AGENT_TOOLS = [load_transactions, filter_transactions]

agent = create_agent(
    model=model,
    tools=TRANSACTION_AGENT_TOOLS
)


def transaction_agent(state: ExpenseState) -> dict[str, Any]:
    """Return only the Transaction Agent's structured JSON result."""
    user_query = state.get("user_query", "").strip()
    print(f"[TransactionAgent] started query={user_query!r}")

    prompt = (
        Path(__file__).resolve().parents[1] / "prompts" / "transaction_agent.prompt"
    ).read_text(encoding="utf-8")

    request_messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_query),
    ]
    
    agent_result = agent.invoke({"messages": request_messages})
    response_messages = agent_result.get("messages")
    if not response_messages:
        raise ValueError("Transaction Agent returned no messages.")

    raw_content = response_messages[-1].content
    try:
        parsed = parse_llm_json(raw_content)
        transaction_result = TransactionResult.model_validate(parsed).model_dump()
    except Exception as error:
        raise ValueError(
            f"Transaction Agent failed: {error}. "
            f"Raw (first 500 chars): {raw_content[:500]}"
        ) from error

    print(
        "[TransactionAgent] completed "
        f"transactions={len(transaction_result.get('transactions', []))}"
    )
    return {"transaction_result": transaction_result}