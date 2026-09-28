import json
from pathlib import Path
from typing import Any

from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage
from model import model
from rag.retrieval import (
	get_retrieval_scores,
	reset_retrieval_scores,
	retrieve_policy_context,
)
from schemas import AnalysisResult, parse_llm_json
from state import ExpenseState

agent = create_agent(
	model=model,
	tools=[retrieve_policy_context]
)


def _summarize_transactions(
	categorized_transactions: list[dict[str, Any]],
) -> dict[str, Any]:
	"""Build a compact summary to reduce tokens sent to the LLM."""
	category_totals: dict[str, dict] = {}
	merchants: dict[str, float] = {}
	dates: list[str] = []

	for t in categorized_transactions:
		cat = t.get("category", "Other")
		amt = t.get("amount", 0)
		if cat not in category_totals:
			category_totals[cat] = {"total": 0, "count": 0, "transactions": []}
		category_totals[cat]["total"] += amt
		category_totals[cat]["count"] += 1
		category_totals[cat]["transactions"].append({
			"id": t.get("transaction_id"),
			"amount": amt,
			"merchant": t.get("merchant"),
			"date": t.get("date"),
			"description": t.get("description"),
		})
		merchants[t.get("merchant", "")] = merchants.get(t.get("merchant", ""), 0) + amt
		if t.get("date"):
			dates.append(t["date"])

	return {
		"total_transactions": len(categorized_transactions),
		"total_spending": sum(c["total"] for c in category_totals.values()),
		"date_range": {"from": min(dates), "to": max(dates)} if dates else {},
		"by_category": category_totals,
		"top_merchants": dict(sorted(merchants.items(), key=lambda x: -x[1])[:10]),
	}


def analysis_agent(state: ExpenseState) -> dict[str, Any]:
	"""Analyze categorized transactions with conditional policy context."""
	user_query = state.get("user_query", "").strip()
	categorized_transactions = state.get("categorized_transactions", [])
	if not user_query:
		raise ValueError("ExpenseState must contain a user_query.")
	if not categorized_transactions:
		raise ValueError("ExpenseState must contain categorized_transactions.")
	print(
		"[AnalysisAgent] started "
		f"transactions={len(categorized_transactions)} query={user_query!r}"
	)

	prompt = (
		Path(__file__).resolve().parents[1] / "prompts" / "analysis_agent.prompt"
	).read_text(encoding="utf-8")

	# Pre-summarize to reduce token usage
	summary = _summarize_transactions(categorized_transactions)
	request_data: dict[str, Any] = {
		"user_query": user_query,
		"transaction_summary": summary,
	}
	reset_retrieval_scores()
	agent_result = agent.invoke({
		"messages": [
			SystemMessage(content=prompt),
			HumanMessage(content=json.dumps(request_data, ensure_ascii=False)),
		]
	})

	response_messages = agent_result.get("messages")
	if not response_messages:
		raise ValueError("Analysis Agent returned no messages.")

	raw_content = response_messages[-1].content
	try:
		parsed = parse_llm_json(raw_content)
		analysis_result = AnalysisResult.model_validate(parsed).model_dump()
	except Exception as error:
		raise ValueError(
			f"Analysis Agent failed: {error}. "
			f"Raw (first 500 chars): {raw_content[:500]}"
		) from error

	print("[AnalysisAgent] completed")

	return {
		"analysis": analysis_result,
		"policy_scores": get_retrieval_scores(),
	}
