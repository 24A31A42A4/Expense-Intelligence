import json
from pathlib import Path
from typing import Any

from langchain.messages import HumanMessage, SystemMessage
from model import model
from schemas import RecommendationResult, parse_llm_json
from state import ExpenseState


def recommendation_agent(state: ExpenseState) -> dict[str, Any]:
	"""Generate recommendations from the Analysis Agent's result."""
	user_query = state.get("user_query", "").strip()
	analysis = state.get("analysis", {})
	categorized_transactions = state.get("categorized_transactions", [])
	if not user_query:
		raise ValueError("ExpenseState must contain a user_query.")
	if not analysis:
		raise ValueError("ExpenseState must contain analysis.")
	print(
		"[RecommendationAgent] started "
		f"categorized_transactions={len(categorized_transactions)}"
	)

	prompt = (
		Path(__file__).resolve().parents[1]
		/ "prompts"
		/ "recommendation_agent.prompt"
	).read_text(encoding="utf-8")
	request = json.dumps({
		"user_query": user_query,
		"analysis": analysis,
		"categorized_transactions": categorized_transactions,
	}, ensure_ascii=False)

	response = model.invoke([
		SystemMessage(content=prompt),
		HumanMessage(content=request),
	])

	raw_content = response.content
	try:
		parsed = parse_llm_json(raw_content)
		recommendation_result = RecommendationResult.model_validate(parsed).model_dump()
	except Exception as error:
		raise ValueError(
			f"Recommendation Agent failed: {error}. "
			f"Raw (first 500 chars): {raw_content[:500]}"
		) from error

	if not recommendation_result.get("recommendations"):
		raise ValueError("Recommendation Agent result is missing recommendations.")

	final_response = recommendation_result.get(
		"final_response",
		recommendation_result.get("summary", ""),
	)
	if not final_response:
		raise ValueError("Recommendation Agent result is missing final_response.")
	print(
		"[RecommendationAgent] completed "
		f"recommendations={len(recommendation_result['recommendations'])}"
	)

	return {
		"recommendations": recommendation_result["recommendations"],
		"final_response": final_response,
	}
