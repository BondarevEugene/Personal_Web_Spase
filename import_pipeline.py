# ==============================================================================
# PROJECT: OMNIFACTORY EVO // AUTOMATED COGNITIVE IMPORT PIPELINE
# LOCATION: /import_pipeline.py
# PURPOSE: Scans raw text documents, chunks them, and provisions ChromaDB indices
# ==============================================================================

import os
import uuid
import logging
import chromadb
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("ImportPipeline")

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "chroma_db_storage")
DATA_SOURCE_DIR = BASE_DIR / "knowledge_source"


def chunk_text(text, max_chars=800, overlap=100):
    """Нарезка текста на перекрывающиеся чанки для сохранения контекста"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start += max_chars - overlap
    return chunks


def run_import_pipeline():
    logger.info("◈ ИНИЦИАЛИЗАЦИЯ КОНВЕЙЕРА ИМПОРТА БАЗЫ ЗНАНИЙ...")

    # Гарантируем наличие папки для сырых текстовых документов
    if not DATA_SOURCE_DIR.exists():
        DATA_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        # Создаем демо-файл, если папка была пуста
        demo_file = DATA_SOURCE_DIR / "readme_core.txt"
        with open(demo_file, "w", encoding="utf-8") as f:
            f.write(
                "Инженерный регламент OmniFactory Evo. Разработка запущена инженером Бондаревым Е. в 2026 году.\n"
                "Система оперирует на порту бэкенда 8089. Модули CRM и Genesys интегрированы через шину асинхронных событий.\n"
                "Локальный AI использует Ollama с кодовой моделью 'codellama' для супервизии генерации рантайм-кода ботов."
            )
        logger.info(f"📁 Создана пустая папка для знаний. Сгенерирован демо-файл: {demo_file}")

    # Подключаемся к персистентному хранилищу ChromaDB
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    collection = chroma_client.get_or_create_collection(name="omnifactory_intelligence")

    total_chunks_added = 0

    # Сканируем все .txt файлы в папке источников знаний
    for file_path in DATA_SOURCE_DIR.glob("*.txt"):
        logger.info(f"📖 Обработка файла: {file_path.name}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                continue

            # Режем файл на чанки
            chunks = chunk_text(content)

            documents = []
            ids = []
            metadatas = []

            for index, chunk in enumerate(chunks):
                documents.append(chunk)
                ids.append(f"chunk_{file_path.stem}_{uuid.uuid4().hex[:8]}")
                metadatas.append({"source": file_path.name, "chunk_index": index})

            # Инжектируем пакет векторов в ChromaDB
            collection.upsert(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            total_chunks_added += len(documents)
            logger.info(f"✓ Успешно импортировано {len(documents)} чанков из файла {file_path.name}")

        except Exception as e:
            logger.error(f"❌ Ошибка при чтении файла {file_path.name}: {str(e)}")

    logger.info(f"🏁 КОНВЕЙЕР ИМПОРТА ЗАВЕРШЕН. Всего активных чанков добавлено в ядро: {total_chunks_added}")

    # ==============================================================================
    # PROJECT: OMNIFACTORY EVO // AUTOMATED MULTI-TENANT IMPORT PIPELINE
    # LOCATION: /import_pipeline.py
    # PURPOSE: Scans text docs, chunks them, and provisions isolated ChromaDB indices
    # ==============================================================================

    import os
    import uuid
    import logging
    import chromadb
    from pathlib import Path

    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
    logger = logging.getLogger("ImportPipeline")

    BASE_DIR = Path(__file__).resolve().parent

    def chunk_text(text, max_chars=800, overlap=100):
        """Нарезка текста на перекрывающиеся чанки для сохранения контекста"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            chunks.append(text[start:end])
            start += max_chars - overlap
        return chunks

    def run_import_pipeline(tenant_id: str = "default"):
        logger.info(f"◈ ИНИЦИАЛИЗАЦИЯ КОНВЕЙЕРА ИМПОРТА ДЛЯ КЛИЕНТА [TENANT: {tenant_id}]...")

        # Динамические пути на основе ID клиента
        tenant_source_dir = BASE_DIR / "tenants_storage" / tenant_id / "knowledge_source"
        tenant_db_path = str(BASE_DIR / "tenants_storage" / tenant_id / "chroma_db_storage")

        # Гарантируем наличие папки для сырых текстовых документов конкретного клиента
        if not tenant_source_dir.exists():
            tenant_source_dir.mkdir(parents=True, exist_ok=True)
            demo_file = tenant_source_dir / "readme_core.txt"
            with open(demo_file, "w", encoding="utf-8") as f:
                f.write(
                    f"Инженерный регламент для {tenant_id}. Разработка OmniFactory Evo в 2026 году.\n"
                    "Система оперирует изолированными контейнерами ботов и RAG-базами."
                )
            logger.info(f"📁 Создана пустая папка знаний клиента. Сгенерирован демо-файл: {demo_file}")

        # Подключаемся к персистентному хранилищу ChromaDB этого клиента
        chroma_client = chromadb.PersistentClient(path=tenant_db_path)
        # Каждому клиенту — своя изолированная коллекция в его базе
        collection = chroma_client.get_or_create_collection(name=f"omnifactory_intelligence_{tenant_id}")

        total_chunks_added = 0

        # Сканируем все .txt файлы в папке источников знаний клиента
        for file_path in tenant_source_dir.glob("*.txt"):
            logger.info(f"📖 Обработка файла: {file_path.name}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if not content.strip():
                    continue

                # Твоя логика нарезки на чанки
                chunks = chunk_text(content)

                documents = []
                ids = []
                metadatas = []

                for index, chunk in enumerate(chunks):
                    documents.append(chunk)
                    ids.append(f"chunk_{tenant_id}_{file_path.stem}_{uuid.uuid4().hex[:8]}")
                    metadatas.append({"source": file_path.name, "chunk_index": index, "tenant": tenant_id})

                # Инжектируем пакет векторов с полной мета-информацией
                collection.upsert(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )
                total_chunks_added += len(documents)
                logger.info(f"✓ Успешно импортировано {len(documents)} чанков из файла {file_path.name}")

            except Exception as e:
                logger.error(f"❌ Ошибка при чтении файла {file_path.name}: {str(e)}")

        logger.info(f"🏁 КОНВЕЙЕР ИМПОРТА ЗАВЕРШЕН. Всего активных чанков в ядре {tenant_id}: {total_chunks_added}")

    if __name__ == "__main__":
        # По умолчанию запускаем для дефолтного пространства
        run_import_pipeline("default")


if __name__ == "__main__":
    run_import_pipeline()