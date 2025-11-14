from typing import Any, Dict, Optional
from pydantic import BaseModel


class TestCaseRequest(BaseModel):
    prompt: str                     # Описание/требование, из которого генерим тест
    prefer_style: Optional[str] = None  # Например, "web" / "mobile" / "detailed" и т.п.
    push_to_qase: bool = False      # Если true — пушим в Qase


class TestCaseResponse(BaseModel):
    testcase: str                   # Сгенерированный текст тест-кейса
    qase_push: Optional[Any] = None # Что вернул Qase (или None, если не пушили)


class AutoTestRequest(BaseModel):
    testcase_text: str              # Текст тест-кейса
    base_url: Optional[str] = None  # Базовый URL для автотеста (опционально)


class AutoTestResponse(BaseModel):
    code: str                       # Сгенерированный код Playwright-теста
