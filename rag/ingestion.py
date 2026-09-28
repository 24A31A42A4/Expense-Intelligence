from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


POLICY_PATH = (
	Path(__file__).resolve().parents[1]
	/ "expense_income_policy_rag_knowledge_base.txt"
)


def ingest_policy_documents(file_path: str | None = None) -> list[Document]:
	"""Load the policy text and split it into RAG-ready documents."""
	source_path = Path(file_path) if file_path else POLICY_PATH
	documents = TextLoader(
		str(source_path),
		encoding="utf-8",
	).load()

	splitter = RecursiveCharacterTextSplitter(
		chunk_size=500,
		chunk_overlap=150,
		length_function=len,
	)
	return splitter.split_documents(documents)
