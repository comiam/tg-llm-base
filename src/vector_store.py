import os
import logging
from typing import List, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_core.embeddings import Embeddings

from .telegram_client import get_client, fetch_messages

# Environment variables should be loaded already from cli.py
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
INDEX_DIR: str = os.getenv("INDEX_DIR", "indexes")


def get_index_path(channel: str) -> str:
    """Возвращает путь для сохранения индекса по имени канала."""
    return os.path.join(INDEX_DIR, f"{channel}_index")


def load_store(index_path: str, embeddings: Embeddings) -> Optional[FAISS]:
    """Загружает индекс из файла."""
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Индекс не найден: {index_path}")

    return FAISS.load_local(
        index_path, embeddings, allow_dangerous_deserialization=True
    )


async def update_index(
    channel: str, filter_fwd_or_replied: bool = True
) -> FAISS:
    """
    Загружает существующий индекс (если есть), определяет последний индексированный message id,
    получает новые сообщения и пересоздаёт индекс с объединёнными документами.

    Args:
        channel: ID или имя канала/группы
        filter_fwd_or_replied: Если True, отбирать только пересланные или с ответом сообщения
    """
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    index_path: str = get_index_path(channel)
    vectorstore: Optional[FAISS] = None
    existing_docs: List[Document] = []

    if os.path.exists(index_path):
        try:
            vectorstore = load_store(index_path, embeddings)
            if hasattr(vectorstore, "docstore") and vectorstore.docstore:
                existing_docs = list(vectorstore.docstore._dict.values())
            logging.info(f"Загружен индекс для канала {channel}")
        except Exception as e:
            logging.error(f"Ошибка загрузки индекса: {e}")

    last_id: int = max(
        (int(doc.metadata.get("id", 0)) for doc in existing_docs),
        default=0,
    )

    client = await get_client()
    new_msgs = await fetch_messages(
        client,
        channel,
        last_id if last_id > 0 else None,
        filter_fwd_or_replied,
    )

    if new_msgs:
        new_docs = await build_docs(new_msgs, client)
        all_docs = existing_docs + new_docs
        logging.info(
            f"Добавлено {len(new_docs)} новых документов. Всего документов: {len(all_docs)}"
        )
        vectorstore = FAISS.from_documents(all_docs, embeddings)
        vectorstore.save_local(index_path)
        logging.info(f"Индекс сохранен в {index_path}")
    else:
        logging.info("Новых сообщений не найдено.")
        if vectorstore is None and existing_docs:
            vectorstore = FAISS.from_documents(existing_docs, embeddings)
            vectorstore.save_local(index_path)

    await client.disconnect()

    return vectorstore


async def build_docs(messages, client) -> List[Document]:
    """Преобразует список сообщений в документы для индексирования."""
    from .telegram_client import process_media_document
    from datetime import datetime

    result_docs = []
    filtered_count = 0
    media_types = {}

    for msg in messages:
        content = msg.message

        if (
            not content
            and hasattr(msg, "media")
            and msg.media
            and type(msg.media).__name__ == "MessageMediaDocument"
        ):
            content = await process_media_document(client, msg)

        if content:
            result_docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "id": msg.id,
                        "date": (
                            msg.date.strftime("%Y-%m-%d %H:%M:%S")
                            if isinstance(msg.date, datetime)
                            else str(msg.date)
                        ),
                        "has_media_document": hasattr(msg, "media")
                        and msg.media
                        and type(msg.media).__name__ == "MessageMediaDocument",
                    },
                )
            )
        else:
            filtered_count += 1
            if hasattr(msg, "media") and msg.media:
                media_type = type(msg.media).__name__
                media_types[media_type] = media_types.get(media_type, 0) + 1
            else:
                media_types["без медиа"] = media_types.get("без медиа", 0) + 1

    logging.info(
        f"Проиндексировано {len(result_docs)} из {len(messages)} сообщений."
    )

    if filtered_count > 0:
        media_summary = ", ".join(
            [f"{mtype}: {count}" for mtype, count in media_types.items()]
        )
        logging.info(
            f"Отсеяно {filtered_count} сообщений с пустым текстом. Типы медиа: {media_summary}"
        )

    return result_docs
