# Telegram LLM Base

[![ru](https://img.shields.io/badge/lang-ru-blue.svg)](https://github.com/comiam/tg-llm-base/blob/master/README.md)

A tool for creating a local knowledge base from Telegram channel/group messages with RAG (Retrieval Augmented Generation) query capabilities.

## Description

Telegram LLM Base allows you to:
- Create and update local vector indices from Telegram channel/group messages
- Filter messages by parameters (forwarded, with replies, etc.)
- Perform semantic queries on indexed messages
- Two operating modes: analytical and technical

## Requirements

- Python 3.9+
- Telegram API credentials (API ID, API Hash)
- OpenAI API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/comiam/tg-llm-base.git
   cd tg_llm_base
   ```

2. Install dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install poetry
   poetry install
   ```

## Configuration

### Getting API Credentials

#### Telegram API
1. Visit [https://my.telegram.org/](https://my.telegram.org/)
2. Log in to your Telegram account
3. Go to the "API development tools" section
4. Create a new application
5. Get your API ID and API Hash

#### OpenAI API
1. Register at [https://platform.openai.com/](https://platform.openai.com/)
2. Go to the API Keys section
3. Create a new API key

### Configuration

1. Create a `.env` file in the project root based on `.env.example`:
   ```
   cp .env.example .env
   ```

2. Edit the `.env` file, specifying:
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_PHONE=your_phone_number
   SESSION_NAME=session_name
   OPENAI_API_KEY=your_openai_api_key
   ```

   Additional parameters:
   ```
   INDEX_DIR=directory_for_indices
   TOP_K=10
   LLM_TEMPERATURE=0.5
   MAX_MESSAGES_TO_FETCH=100000
   TECH_SPEC_MODEL=gpt-4
   ANALYSIS_MODEL=gpt-4
   ```

## Usage

### Getting a list of available groups/channels

```
python cli.py list-groups
```

### Creating/updating an index

```
python cli.py update --channel "<username/id of channel or chat>"
```

or with filtering only forwarded messages:

```
python cli.py update --channel "<username/id of channel or chat>" --fwd
```

### Executing queries

#### Single query

```
python cli.py query --channel "<username/id of channel or chat>" --query "Your query"
```

#### Interactive mode

```
python cli.py query --channel "<username/id of channel or chat>"
```

#### Additional query parameters

- `--update`: update the index before querying
- `--fwd`: filter and index only forwarded messages
- `--mode tech_spec|analysis`: select mode (technical or analytical)

**Note:**<br/>
`--fwd` is needed if you store separate channel posts somewhere. And you need to index specifically them.

Example:
```
python cli.py query --channel @some_channel --mode tech_spec --update
# or
python cli.py query --channel "-1345677564" --mode tech_spec --update
```

## Limitations

- Access to Telegram API and OpenAI API is required
- Full access to your Telegram account (phone number) is required for comprehensive Telegram functionality
- Channels/groups must be accessible from your Telegram account

## License

This project is distributed under the Mozilla Public License Version 2.0.

## Author
Comiam
