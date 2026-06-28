# ==============================================================================
# PROJECT: PERSONAL_WEB_SPACE
# LOCATION: /backend/modules/ai_consultant.py
# VERSION: 1.1.0
# LAST MODIFIED: 2026-05-19
# DESCRIPTION: Модуль интеллектуального консультанта с RAG-системой.
#              Интегрирован с панелью оркестрации SYSTEM_CORE_ORCHESTRATOR.
# PURPOSE: Обработка вопросов пользователей на основе базы знаний (ChromaDB)
#          через модель Gemini с поддержкой динамического включения/выключения.
# DEPENDENCIES: langchain, langchain_google_genai, chromadb
# AUTHORS: Human & AI Collaboration
# STATUS: Ready for Orchestration Integration
# ==============================================================================
import os
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

# Глобальный флаг
IS_ACTIVE = True


def set_module_status(status: bool):
    global IS_ACTIVE
    IS_ACTIVE = status


def get_ai_response(user_query: str, vector_db_path: str) -> dict:
    if not IS_ACTIVE:
        return {
            "status": "restricted",
            "error": "SERVICE_TEMPORARILY_UNAVAILABLE",
            "response": "Модуль ИИ-консультанта отключен.",
        }

    api_key = os.getenv("GOOGLE_API_KEY", "YOUR_API_KEY")

    try:
        llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

        if not os.path.exists(vector_db_path):
            return {
                "status": "error",
                "error": "VECTOR_DB_NOT_FOUND",
                "response": "База знаний не обнаружена.",
            }

        # Инициализация векторной базы
        db = Chroma(persist_directory=vector_db_path)
        retriever = db.as_retriever(search_kwargs={"k": 3})

        # Современный шаблон промпта
        prompt = ChatPromptTemplate.from_template("""
        Ответь на вопрос пользователя, основываясь только на предоставленном контексте.
        Если ответа нет в контексте, скажи, что не знаешь.

        Контекст: {context}

        Вопрос: {input}
        """)

        # Создание цепочек (вместо устаревшего RetrievalQA)
        combine_docs_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

        # Выполнение запроса
        result = retrieval_chain.invoke({"input": user_query})

        return {"status": "success", "response": result["answer"]}

    except Exception as e:
        return {"status": "error", "error": str(e), "response": "Core Processing Failure."}