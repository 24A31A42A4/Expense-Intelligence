import os

from dotenv import load_dotenv
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)

load_dotenv()

google_api_key = os.getenv("gemini_api_key")
google_chat_api_key = os.getenv("gemini_api_key2") or google_api_key


primary_chat_model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=google_chat_api_key,
)

if google_api_key and google_chat_api_key != google_api_key:
    secondary_chat_model = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=google_api_key,
    )
    model = primary_chat_model.with_fallbacks([secondary_chat_model])
else:
    model = primary_chat_model

embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=google_api_key,
)
