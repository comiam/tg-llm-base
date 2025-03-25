# Telegram LLM Base

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/comiam/tg-llm-base/blob/master/README.en.md)

Инструмент для создания локальной базы знаний из сообщений Telegram каналов/групп с возможностью RAG запросов к этой базе.

## Описание

Telegram LLM Base позволяет:
- Создавать и обновлять локальные векторные индексы из сообщений каналов/групп в Telegram
- Фильтровать сообщения по параметрам (пересланные, с ответами и т.д.)
- Выполнять семантические запросы к индексированным сообщениям
- Два режима работы: аналитический и технический

## Требования

- Python 3.9+
- Telegram API данные (API ID, API Hash)
- OpenAI API ключ

## Установка

1. Клонировать репозиторий:
   ```
   git clone https://github.com/comiam/tg-llm-base.git
   cd tg_llm_base
   ```

2. Установить зависимости:
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install poetry
   poetry install
   ```

## Настройка

### Получение API данных

#### Telegram API
1. Посетите [https://my.telegram.org/](https://my.telegram.org/)
2. Войдите в свой аккаунт Telegram
3. Перейдите в раздел "API development tools"
4. Создайте новое приложение
5. Получите API ID и API Hash

#### OpenAI API
1. Зарегистрируйтесь на [https://platform.openai.com/](https://platform.openai.com/)
2. Перейдите в раздел API Keys
3. Создайте новый API ключ

### Конфигурация

1. Создайте файл `.env` в корне проекта на основе `.env.example`:
   ```
   cp .env.example .env
   ```

2. Отредактируйте файл `.env`, указав:
   ```
   TELEGRAM_API_ID=ваш_api_id
   TELEGRAM_API_HASH=ваш_api_hash
   TELEGRAM_PHONE=ваш_номер_телефона
   SESSION_NAME=имя_сессии
   OPENAI_API_KEY=ваш_openai_api_key
   ```

   Дополнительные параметры:
   ```
   INDEX_DIR=директория_для_индексов
   TOP_K=10
   LLM_TEMPERATURE=0.5
   MAX_MESSAGES_TO_FETCH=100000
   TECH_SPEC_MODEL=gpt-4
   ANALYSIS_MODEL=gpt-4
   ```

## Использование

### Получение списка доступных групп/каналов

```
python cli.py list-groups
```

### Создание/обновление индекса

```
python cli.py update --channel "<username/id канала или чата>"
```

или с фильтрацией только пересланных сообщений:

```
python cli.py update --channel "<username/id канала или чата>" --fwd
```

### Выполнение запросов

#### Одиночный запрос

```
python cli.py query --channel "<username/id канала или чата>" --query "Ваш запрос"
```

#### Интерактивный режим

```
python cli.py query --channel "<username/id канала или чата>"
```

#### Дополнительные параметры запроса

- `--update`: обновить индекс перед запросом
- `--fwd`: фильтровать и оставлять при индексации только пересланные сообщения
- `--mode tech_spec|analysis`: выбор режима (технический или аналитический)

**Примечание:**<br/>
`--fwd` нужен, если складируете отдельные посты каналов у себя где-либо. И именно их вам надо проиндексировать.

Пример:
```
python cli.py query --channel @some_channel --mode tech_spec --update
# или
python cli.py query --channel "-1345677564" --mode tech_spec --update
```

## Ограничения

- Для работы необходим доступ к Telegram API и OpenAI API
- Для полноценной работы с Telegram потребуется полный доступ к аккаунту (номер телефона)
- Каналы/группы должны быть доступны с вашего аккаунта Telegram

## Лицензия

Проект распространяется под лицензией Mozilla Public License Version 2.0.

## Автор
Comiam
