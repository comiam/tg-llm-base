import os
import logging
from typing import Dict
import re


class PromptManager:
    """Класс для управления системными промптами."""

    def __init__(self, prompts_dir: str):
        """
        Инициализирует менеджер промптов.

        Args:
            prompts_dir: Директория, где хранятся файлы с промптами
        """
        self.prompts_dir = prompts_dir
        self.system_prompts: Dict[str, str] = {}

        os.makedirs(self.prompts_dir, exist_ok=True)
        self.load_prompts()

    def load_prompts(self) -> None:
        """Загружает системные промпты из файлов."""
        prompt_files = [
            f
            for f in os.listdir(self.prompts_dir)
            if re.fullmatch(r".*_prompt\.md$", f)
        ]

        for prompt_file in prompt_files:
            key = os.path.splitext(prompt_file)[0].replace("_prompt", "")
            full_path = os.path.join(self.prompts_dir, prompt_file)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    self.system_prompts[key] = f.read().strip()
                logging.debug(
                    f"Загружен промпт для ключа '{key}' из {full_path}"
                )
            except Exception as e:
                logging.error(f"Ошибка при загрузке ключа '{key}': {e}")

    def get_prompt(self, prompt_key: str) -> str:
        """
        Возвращает системный промпт для указанного ключа.

        Args:
            prompt_key: Ключ промпта, например, "tech_spec"

        Returns:
            Системный промпт для указанного ключа
        """
        if prompt_key not in self.system_prompts:
            raise ValueError(f"Промпт для ключа '{prompt_key}' не найден")

        return self.system_prompts.get(prompt_key)
