from pathlib import Path

from langchain_chroma import Chroma

from model import embedding_model
from rag.ingestion import ingest_policy_documents


VECTOR_DB_PATH = Path(__file__).resolve().parents[1] / "rag_vector_db"
COLLECTION_NAME = "expense_income_policy_collection"


def build_policy_vector_store(
	persist_directory: str | None = None,
) -> Chroma:
	"""Create or update the persistent Chroma policy collection."""
	storage_path = Path(persist_directory) if persist_directory else VECTOR_DB_PATH
	storage_path.mkdir(parents=True, exist_ok=True)

	vector_store = Chroma(
		collection_name=COLLECTION_NAME,
		embedding_function=embedding_model,
		persist_directory=str(storage_path),
	)

	documents = ingest_policy_documents()
	document_ids = [f"policy-chunk-{index}" for index in range(len(documents))]
	existing_ids = set(vector_store.get()["ids"])
	new_documents = [
		(document, document_id)
		for document, document_id in zip(documents, document_ids)
		if document_id not in existing_ids
	]
	if new_documents:
		vector_store.add_documents(
			[document for document, _ in new_documents],
			ids=[document_id for _, document_id in new_documents],
		)

	return vector_store
