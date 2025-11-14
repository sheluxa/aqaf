import re
import json
import requests
from typing import List, Dict

# ❗ ВСТАВЬ СВОЙ ТОКЕН И КОД ПРОЕКТА СЮДА
TOKEN = "e6c7018e07a586e79f6e6f503766a9cf13260949f37068d85c62db094dd998fe"
PROJECT = "AQA"  # например: AQA
SUITE_ID = None  # можешь указать ID сьюта (число), если хочешь

QASE_API = "https://api.qase.io/v1"

HEADERS = {
    "Token": TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def _parse_title(text: str) -> str:
    m = re.search(r"Название:\s*(.+)", text)
    return m.group(1).strip() if m else "Автоматически сгенерированный тест"


def _parse_preconditions(text: str) -> str:
    m = re.search(r"Предусловие:\s*(.+)", text)
    return m.group(1).strip() if m else ""


def _parse_steps(text: str) -> List[Dict[str, str]]:
    """
    Ожидаем формат:
      N) <действие>
         ОР: <ожидаемый результат>
    """
    lines = text.splitlines()
    steps: List[Dict[str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r"\d+\)\s*(.+)", line)
        if m:
            action = m.group(1).strip()
            expected = ""
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                m2 = re.match(r"(ОР|OR)\s*:\s*(.+)", nxt, flags=re.IGNORECASE)
                if m2:
                    expected = m2.group(2).strip()
                    i += 1
            steps.append({"action": action, "expected_result": expected})
        i += 1
    return steps


def push_to_qase(testcase_markdown: str) -> dict:
    """
    Реальная отправка тест-кейса в Qase.io.
    """
    if not TOKEN or not PROJECT:
        return {"status": "error", "message": "TOKEN или PROJECT не задан в qase_client.py"}

    title = _parse_title(testcase_markdown)
    pre = _parse_preconditions(testcase_markdown)
    steps = _parse_steps(testcase_markdown)

    payload: Dict[str, object] = {
        "title": title,
        "description": testcase_markdown,
        "preconditions": pre,
        "postconditions": "",
        "severity": 2,  # Normal
        "priority": 2,  # Medium
        "behavior": 1,  # Positive
        "type": 1,      # Functional
        "status": 1,    # Actual
    }
    if SUITE_ID:
        payload["suite_id"] = SUITE_ID
    if steps:
        payload["steps"] = steps

    url = f"{QASE_API}/case/{PROJECT}"

    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=15)
        if r.status_code == 200:
            return {"status": "ok", "qase": r.json()}
        else:
            return {"status": "error", "code": r.status_code, "response": r.text}
    except Exception as e:
        return {"status": "exception", "error": str(e)}
