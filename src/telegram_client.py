import os
import logging
from typing import List, Optional, Tuple

from telethon import TelegramClient
from telethon.tl.types import Message

API_ID: str = os.getenv("TELEGRAM_API_ID", "")
API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
PHONE: str = os.getenv("TELEGRAM_PHONE", "")
SESSION_NAME: str = os.getenv("SESSION_NAME", "session_name")

MAX_MESSAGES_TO_FETCH: int = int(os.getenv("MAX_MESSAGES_TO_FETCH", "100000"))


async def get_client() -> TelegramClient:
    """Создаёт и возвращает подключённого TelegramClient."""
    client = TelegramClient(
        session=SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        app_version="1.01",
        system_version="4.1.30-vcUSTOM",
        device_model="Comiam Ubuntu PC",
    )
    await client.start(PHONE)
    return client


async def fetch_messages(
    client: TelegramClient,
    channel: str,
    last_id: Optional[int] = None,
    filter_fwd_or_replied: bool = True,
) -> List[Message]:
    """
    Получает сообщения из заданного канала/группы, отбирая пересланные сообщения
    или с reply-ссылкой. Если last_id указан, выбираются сообщения с id > last_id.

    Args:
        client: Telegram клиент
        channel: ID или имя канала/группы
        last_id: ID последнего полученного сообщения для продолжения
        filter_fwd_or_replied: Если True, отбирать только пересланные или с ответом сообщения
    """
    channel = channel.strip()
    channel_id = int(channel) if channel.lstrip("-+").isdigit() else channel
    entity = await client.get_input_entity(channel_id)

    logging.info(f"Получение сообщений из канала {channel}")
    logging.info(f"Последний ID сообщения: {last_id if last_id else 0}")

    messages: List[Message] = [
        msg
        async for msg in client.iter_messages(
            entity, limit=MAX_MESSAGES_TO_FETCH
        )
        if (not filter_fwd_or_replied or (msg.fwd_from or msg.reply_to_msg_id))
        and (last_id is None or msg.id > last_id)
    ]

    logging.info(f"Найдено {len(messages)} новых сообщений в канале {channel}")
    return messages


async def process_media_document(
    client: TelegramClient, msg: Message
) -> Optional[str]:
    """Извлекает текст из документов."""
    if (
        not hasattr(msg, "media")
        or not msg.media
        or not hasattr(msg.media, "document")
    ):
        return None

    try:
        doc = msg.media.document
        mime_type = None
        file_name = None

        for attr in doc.attributes:
            if hasattr(attr, "mime_type"):
                mime_type = attr.mime_type
            if hasattr(attr, "file_name"):
                file_name = attr.file_name

        # Только текстовые документы
        if mime_type and (
            "text/" in mime_type or "application/pdf" in mime_type
        ):
            temp_path = f"/tmp/tg_doc_{msg.id}"
            await client.download_media(message=msg, file=temp_path)

            with open(temp_path, "r", errors="ignore") as f:
                content = f.read()

            os.remove(temp_path)

            return f"[Документ: {file_name or 'без имени'}] {content}"
    except Exception as e:
        logging.warning(
            f"Не удалось обработать документ в сообщении {msg.id}: {e}"
        )

    return None


async def list_groups() -> List[Tuple[str, str]]:
    """
    Подключается к Telegram через единый клиент и возвращает список диалогов.
    Возвращает список кортежей (название, username).
    """
    client = await get_client()
    dialogs = await client.get_dialogs()
    groups: List[Tuple[str, str]] = []

    for dialog in dialogs:
        username = None
        if hasattr(dialog.entity, "username") and dialog.entity.username:
            username = f"@{dialog.entity.username}"
        elif hasattr(dialog.entity, "id"):
            username = f"id:{dialog.entity.id}"

        if username:
            groups.append((dialog.title, username))

    await client.disconnect()
    return groups
