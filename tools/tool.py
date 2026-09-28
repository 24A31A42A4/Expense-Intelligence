import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from langchain.tools import tool
from pydantic import BaseModel


CSV_PATH = Path(__file__).resolve().parents[1] / "expense_transactions_3_months_2026.csv"
CSV_FIELDS = {
    "transaction_id",
    "date",
    "description",
    "amount",
    "payment_method",
    "merchant",
    "location",
    "transaction_type",
}


class TransactionRecord(BaseModel):
    transaction_id: str
    transaction_date: date
    description: str
    amount: float
    payment_method: str
    merchant: str
    location: str
    transaction_type: str


def _read_transactions(file_path: str | None = None) -> list[TransactionRecord]:
    source_path = Path(file_path) if file_path else CSV_PATH
    with source_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        headings = set(reader.fieldnames or [])
        if headings != CSV_FIELDS:
            missing = sorted(CSV_FIELDS - headings)
            unexpected = sorted(headings - CSV_FIELDS)
            raise ValueError(
                f"CSV headings do not match. Missing: {missing}; Unexpected: {unexpected}"
            )

        records = [
            TransactionRecord(
                transaction_id=row["transaction_id"],
                transaction_date=row["date"],
                description=row["description"],
                amount=row["amount"],
                payment_method=row["payment_method"],
                merchant=row["merchant"],
                location=row["location"],
                transaction_type=row["transaction_type"],
            )
            for row in reader
        ]

    transaction_ids = [record.transaction_id for record in records]
    if len(transaction_ids) != len(set(transaction_ids)):
        raise ValueError("Duplicate transaction_id values were found in the CSV.")
    return records


def _as_dict(record: TransactionRecord) -> dict[str, Any]:
    return {
        "transaction_id": record.transaction_id,
        "date": record.transaction_date.isoformat(),
        "description": record.description,
        "amount": record.amount,
        "payment_method": record.payment_method,
        "merchant": record.merchant,
        "location": record.location,
        "transaction_type": record.transaction_type,
    }


@tool
def load_transactions() -> str:
    """Load and validate transaction data using the CSV headings."""
    return json.dumps(
        [_as_dict(record) for record in _read_transactions()],
        ensure_ascii=False,
    )


@tool
def filter_transactions(
    date_from: str | None = None,
    date_to: str | None = None,
    merchant: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    payment_method: str | None = None,
    transaction_type: str | None = None,
) -> str:
    """Filter CSV transactions using only conditions provided by the query."""
    start_date = date.fromisoformat(date_from) if date_from else None
    end_date = date.fromisoformat(date_to) if date_to else None
    if start_date and end_date and start_date > end_date:
        raise ValueError("date_from must be earlier than or equal to date_to.")

    records = _read_transactions()
    filtered = []
    for record in records:
        if start_date and record.transaction_date < start_date:
            continue
        if end_date and record.transaction_date > end_date:
            continue
        if merchant and merchant.lower() not in record.merchant.lower():
            continue
        if min_amount is not None and record.amount < min_amount:
            continue
        if max_amount is not None and record.amount > max_amount:
            continue
        if payment_method and record.payment_method.lower() != payment_method.lower():
            continue
        if transaction_type and record.transaction_type.lower() != transaction_type.lower():
            continue
        filtered.append(_as_dict(record))

    return json.dumps(filtered, ensure_ascii=False)
