import json
from typing import Any

from langchain.tools import tool

from rag.vector_db import build_policy_vector_store


_last_retrieval_scores: list[dict[str, Any]] = []


def reset_retrieval_scores() -> None:
	_last_retrieval_scores.clear()


def get_retrieval_scores() -> list[dict[str, Any]]:
	return list(_last_retrieval_scores)


@tool
def retrieve_policy_context(user_question: str) -> str:
	"""Retrieve relevant policy chunks from Chroma using the full user question."""
	full_query = user_question.strip()
	if not full_query:
		raise ValueError("user_question must not be empty.")

	_last_retrieval_scores.clear()
	vector_store = build_policy_vector_store()
	matches = vector_store.similarity_search_with_relevance_scores(full_query, k=3)
	if not matches:
		return "No relevant policy information was found."

	_context = []
	for document, score in matches:
		_last_retrieval_scores.append({
			"score": round(float(score), 4),
			"source": document.metadata.get("source", "policy knowledge base"),
			"preview": document.page_content[:240],
		})
		_context.append(
			f"Semantic relevance score: {float(score):.4f}\n"
			f"{document.page_content}"
		)

	return json.dumps({
		"policy_context": "\n\n".join(_context),
		"semantic_matches": _last_retrieval_scores,
	}, ensure_ascii=False)
