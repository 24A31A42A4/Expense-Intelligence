from typing import Any, TypedDict


class ExpenseState(TypedDict):
    user_query: str
    transaction_result: dict[str, Any]
    categorized_transactions: list[dict[str, Any]]
    analysis: dict[str, Any]
    recommendations: list[dict[str, Any]]
    final_response: str
    policy_context: list[dict[str, Any]]
    policy_scores: list[dict[str, Any]]
