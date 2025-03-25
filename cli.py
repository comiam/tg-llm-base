#!/usr/bin/env python3
"""
Основная точка входа для запуска Telegram LLM Base.
"""

import argparse
from src.app import run_app, Mode


def cli_main():
    parser = argparse.ArgumentParser(
        description="CLI для работы с Telegram и локальным RAG (FAISS CPU)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    update_parser = subparsers.add_parser(
        "update", help="Обновить или создать индекс RAG"
    )
    update_parser.add_argument(
        "--channel",
        type=str,
        required=True,
        help="USERNAME/ID канала/группы",
    )
    update_parser.add_argument(
        "--fwd",
        action="store_true",
        help="Фильтровать только пересланные или сообщения с ответом",
    )

    query_parser = subparsers.add_parser("query", help="Запрос для выполнения")
    query_parser.add_argument(
        "--channel",
        type=str,
        required=True,
        help="USERNAME/ID канала/группы",
    )
    query_parser.add_argument(
        "--query",
        type=str,
        help="Запрос для выполнения (если не указан, интерактивный режим)",
    )
    query_parser.add_argument(
        "--update", action="store_true", help="Обновить индекс перед запросом"
    )
    query_parser.add_argument(
        "--fwd",
        action="store_true",
        help="Фильтровать только пересланные и сообщения с ответом",
    )
    query_parser.add_argument(
        "--mode",
        type=str,
        choices=[mode.value for mode in Mode],
        default=Mode.ANALYSIS.value,
        help=f"Формат ответа: {Mode.ANALYSIS.value} - стандартный режим, {Mode.TECH_SPEC.value} - режим с инструментами для анализа и перехода по ссылкам",
    )

    subparsers.add_parser(
        "list-groups",
        help="Получить список групп/каналов с USERNAME/ID",
    )

    args = parser.parse_args()
    run_app(args)


if __name__ == "__main__":
    cli_main()
