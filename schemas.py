"""Pydantic response schemas for each agent in the expense pipeline."""

import json
import re
from typing import Any

from pydantic import BaseModel, Field


def parse_llm_json(text: Any) -> dict[str, Any]:
    """Extract and parse JSON from raw LLM text output.

    Handles: plain JSON, markdown-fenced JSON, or JSON embedded in text.
    """
    if isinstance(text, list):
        text = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in text
        )
    elif not isinstance(text, str):
        text = str(text)

    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip markdown code fences
    fenced = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: find the first { ... } block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not extract JSON. Raw (first 500 chars): {text[:500]}"
    )



# ── Transaction Agent ──────────────────────────────────────────────────────


class TransactionItem(BaseModel):
    transaction_id: str
    date: str
    description: str
    amount: float
    payment_method: str
    merchant: str
    location: str
    transaction_type: str


class TransactionResult(BaseModel):
    query: str = Field(description="The original user query")
    filters_applied: dict = Field(default_factory=dict)
    transactions: list[TransactionItem] = Field(default_factory=list)
    total_transactions: int = 0


# ── Category Agent ─────────────────────────────────────────────────────────


class CategorizedTransaction(BaseModel):
    transaction_id: str
    date: str
    description: str
    amount: float
    payment_method: str
    merchant: str
    location: str
    transaction_type: str
    category: str = Field(
        description="One of: Food, Transport, Shopping, Travel, Utilities, "
        "Entertainment, Healthcare, Subscriptions, Other"
    )


class CategoryResult(BaseModel):
    query: str = Field(description="The original user query")
    categorized_transactions: list[CategorizedTransaction] = Field(
        default_factory=list
    )
    total_transactions: int = 0


# ── Analysis Agent ─────────────────────────────────────────────────────────


class AnalysisResult(BaseModel):
    query: str = Field(description="The original user query")
    metrics: dict = Field(default_factory=dict)
    category_analysis: list[str | dict[str, Any]] = Field(default_factory=list)
    patterns: list[str | dict[str, Any]] = Field(default_factory=list)
    anomalies: list[str | dict[str, Any]] = Field(default_factory=list)
    policy_evaluation: list[str | dict[str, Any]] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)


# ── Recommendation Agent ──────────────────────────────────────────────────


class Recommendation(BaseModel):
    action: str = Field(description="Specific recommended action")
    reason: str = Field(description="Evidence from the analysis")
    target_amount: float | None = None
    priority: str = Field(default="medium")


class RecommendationResult(BaseModel):
    query: str = Field(description="The original user query")
    recommendations: list[Recommendation] = Field(default_factory=list)
    summary: str = Field(default="", description="Short answer to the user's query")
    final_response: str = Field(
        description="Complete natural-language response to display in the chat"
    )
