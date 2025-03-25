import asyncio
import argparse
import os
import logging
from typing import Optional, Any
import dotenv
from enum import Enum

from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.callbacks import get_openai_callback
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains.history_aware_retriever import (
    create_history_aware_retriever,
)

from .prompt_manager import PromptManager
from .telegram_client import list_groups
from .vector_store import update_index, get_index_path, load_store

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

dotenv.load_dotenv()

API_ID: str = os.getenv("TELEGRAM_API_ID", "")
API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
PHONE: str = os.getenv("TELEGRAM_PHONE", "")  # +79991234567
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
SESSION_NAME: str = os.getenv("SESSION_NAME", "session_name")
INDEX_DIR: str = os.getenv("INDEX_DIR", "indexes")

TECH_SPEC_MODEL: str = os.getenv("TECH_SPEC_MODEL", "gpt-4")
ANALYSIS_MODEL: str = os.getenv("ANALYSIS_MODEL", "gpt-4")
TOP_K: int = int(os.getenv("TOP_K", "10"))
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.5"))

PROMPTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "prompts"
)

if not all([API_ID, API_HASH, PHONE, OPENAI_API_KEY]):
    missing = []
    if not API_ID:
        missing.append("TELEGRAM_API_ID")
    if not API_HASH:
        missing.append("TELEGRAM_API_HASH")
    if not PHONE:
        missing.append("TELEGRAM_PHONE")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    raise ValueError(
        f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}"
    )

os.makedirs(INDEX_DIR, exist_ok=True)


class Mode(str, Enum):
    """Режимы работы модели."""

    TECH_SPEC = "tech_spec"
    ANALYSIS = "analysis"


def create_qa_chain(
    vectorstore: FAISS,
    prompt_manager: PromptManager,
    mode: Mode = Mode.TECH_SPEC,
) -> Any:
    """
    Создаёт и возвращает цепочку retrieval chain с учетом истории диалога для заданного режима.
    Использует современный подход с create_retrieval_chain и create_history_aware_retriever.
    """

    match mode:
        case Mode.TECH_SPEC:
            model_name = TECH_SPEC_MODEL
        case Mode.ANALYSIS:
            model_name = ANALYSIS_MODEL
        case _:
            raise ValueError(
                f"Неизвестный режим: {mode}. Используйте '{Mode.TECH_SPEC}' или '{Mode.ANALYSIS}'."
            )

    system_prompt = prompt_manager.get_prompt(mode.value)

    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model_name=model_name,
        temperature=LLM_TEMPERATURE,
        max_retries=3,
    )

    base_retriever = vectorstore.as_retriever(
        search_type="similarity", search_kwargs={"k": TOP_K}
    )

    # Используем промпты из PromptManager вместо хардкода
    retrieval_query_prompt = prompt_manager.get_prompt("retrieval_query")
    retrieval_query_format = prompt_manager.get_prompt(
        "retrieval_query_format"
    )

    chat_history_query_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(retrieval_query_prompt),
            HumanMessagePromptTemplate.from_template(retrieval_query_format),
        ]
    )

    # Создаем retriever с учетом истории диалога
    history_aware_retriever = create_history_aware_retriever(
        llm=llm, retriever=base_retriever, prompt=chat_history_query_prompt
    )

    # Создаем промпт для формирования ответа, используя шаблон из PromptManager
    answer_format = prompt_manager.get_prompt("answer_format")
    answer_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(answer_format),
        ]
    )

    # Создаем цепочку для обработки документов
    document_chain = create_stuff_documents_chain(
        llm=llm, prompt=answer_prompt
    )

    # Создаем общую цепочку для работы с запросом и ретривером
    retrieval_chain = create_retrieval_chain(
        retriever=history_aware_retriever, combine_docs_chain=document_chain
    )

    return retrieval_chain


async def query_mode(
    channel: str, init_query: Optional[str] = None, mode: Mode = Mode.TECH_SPEC
) -> None:
    """
    Загружает индекс для заданного канала и выполняет запросы.
    Если передан init_query – выполняется сразу, иначе интерактивный режим.
    Использует одну и ту же цепочку для всех запросов для поддержки истории диалога.
    """
    index_path: str = get_index_path(channel)
    if not os.path.exists(index_path):
        logging.error(
            f"Индекс для канала {channel} не найден. Сначала выполните update."
        )
        return

    prompt_manager = PromptManager(PROMPTS_DIR)
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    try:
        vectorstore = load_store(index_path, embeddings)
        logging.info(f"Загружен индекс для канала {channel}")
    except Exception as e:
        logging.error(f"Ошибка загрузки индекса: {e}")
        return

    try:
        chain = create_qa_chain(vectorstore, prompt_manager, mode)

        chat_history = []
        with get_openai_callback() as cb:
            if init_query:
                # Выполняем единичный запрос
                result = chain.invoke(
                    {"input": init_query, "chat_history": chat_history}
                )
                answer = result["answer"]

                logging.info(f"Ответ ({mode}): {answer}")
            else:
                # Интерактивный режим
                logging.info(
                    "Вход в режим запросов (введите 'exit' для завершения):"
                )

                while (
                    user_query := input("Введите запрос: ").strip().lower()
                ) not in {"выход", "exit"}:
                    result = chain.invoke(
                        {"input": user_query, "chat_history": chat_history}
                    )
                    answer = result["answer"]

                    # Обновляем историю
                    chat_history.append(HumanMessage(content=user_query))
                    chat_history.append(AIMessage(content=answer))
                    logging.info(f"Ответ ({mode}): {answer}")

            logging.info(f"Всего токенов: {cb.total_tokens}")
            logging.info(f"Стоимость: {cb.total_cost}$")
    except ValueError as e:
        logging.error(str(e))
    except Exception as e:
        logging.error(f"Произошла ошибка: {str(e)}")


async def show_groups() -> None:
    """
    Выводит список доступных групп и каналов.
    """
    groups = await list_groups()
    if groups:
        for title, username in groups:
            logging.info(
                f"{'Название:':<20} {title:<30} | {'Username:':<10} {username}"
            )
    else:
        logging.info("Не найдено групп/каналов с CHANNEL_USERNAME.")


def run_app(args: argparse.Namespace) -> None:
    match args.command:
        case "update":
            filter_fwd = getattr(args, "fwd", False)
            asyncio.run(update_index(args.channel, filter_fwd))
        case "query":
            mode = Mode(args.mode)
            filter_fwd = getattr(args, "fwd", True)
            if args.update:
                asyncio.run(update_index(args.channel, filter_fwd))
            asyncio.run(query_mode(args.channel, args.query, mode))
        case "list-groups":
            asyncio.run(show_groups())
