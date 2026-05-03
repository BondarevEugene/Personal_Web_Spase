# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /backend/modules/ai_consultant.py
# VERSION: 1.0.0
# LAST MODIFIED: 2026-05-02
# DESCRIPTION: Модуль интеллектуального консультанта с RAG-системой.
# PURPOSE: Обработка вопросов пользователей на основе базы знаний.
# DEPENDENCIES: langchain, google-generativeai, chromadb
# AUTHORS: Human & AI Collaboration
# STATUS: Development
# ==============================================================================

from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma


def get_ai_response(user_query: str, vector_db_path: str):
    """
    Ищет релевантную информацию в базе знаний и формирует ответ через Gemini.
    """
    llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key="YOUR_API_KEY")

    # Загружаем базу знаний (например, инфу о мебели)
    db = Chroma(persist_directory=vector_db_path)
    retriever = db.as_retriever(search_kwargs={"k": 3})

    # Создаем цепочку: Контекст + Вопрос = Умный ответ
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever
    )

    return qa_chain.run(user_query)