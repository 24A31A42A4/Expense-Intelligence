import json
from pathlib import Path
from typing import Any

from langchain.messages import HumanMessage, SystemMessage
from model import model
from schemas import CategoryResult, parse_llm_json
from state import ExpenseState


def category_agent(state: ExpenseState) -> dict[str, Any]:
	"""Categorize transactions returned by the Transaction Agent."""
	user_query = state.get("user_query", "").strip()
	if not user_query:
		raise ValueError("ExpenseState must contain a user_query.")

	transaction_result = state.get("transaction_result")
	if not transaction_result:
		raise ValueError("ExpenseState must contain a transaction_result.")
	print(
		"[CategoryAgent] started "
		f"transactions={len(transaction_result.get('transactions', []))}"
	)

	prompt = (
		Path(__file__).resolve().parents[1] / "prompts" / "category_agent.prompt"
	).read_text(encoding="utf-8")
	request = json.dumps({
		"user_query": user_query,
		"transaction_result": transaction_result,
	}, ensure_ascii=False)

	response = model.invoke([
		SystemMessage(content=prompt),
		HumanMessage(content=request),
	])

	raw_content = response.content
	try:
		parsed = parse_llm_json(raw_content)
		category_result = CategoryResult.model_validate(parsed).model_dump()
	except Exception as error:
		raise ValueError(
			f"Category Agent failed: {error}. "
			f"Raw (first 500 chars): {raw_content[:500]}"
		) from error

	if not category_result.get("categorized_transactions"):
		raise ValueError(
			"Category Agent result is missing categorized_transactions."
		)
	print(
		"[CategoryAgent] completed "
		f"categorized_transactions={len(category_result['categorized_transactions'])}"
	)

	return {
		"categorized_transactions": category_result["categorized_transactions"],
	}
