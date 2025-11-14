import os
import pandas as pd

from services.qase_client import push_to_qase

# Путь к твоему Excel с тестами
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "test-cases-2025-11-12T22-44-02-177Z (2).xlsx")


def row_to_markdown(row) -> str:
    """
    Собираем текст тест-кейса в том же формате, что возвращает /generate/testcase,
    чтобы наш push_to_qase смог корректно распарсить title / предусловия / шаги.
    Ориентируемся на структуру "Demiand - Рецепты - Авторизация".
    """

    title = str(row.get("Название") or row.get("Название:") or "").strip()
    if not title:
        title = "Автоматически импортированный тест"

    pre = str(row.get("Предусловие") or "").strip()
    if not pre:
        pre = "Не указано"

    steps_text = str(row.get("Шаги") or "").strip()
    exp_text = str(row.get("Ожидаемый результат шага") or "").strip()

    # Простая эвристика: шаги и ожидания хранятся многострочно
    steps_lines = [s for s in steps_text.splitlines() if s.strip()]
    exp_lines = [s for s in exp_text.splitlines() if s.strip()]

    lines = []
    lines.append(f"Название: {title}")
    lines.append(f"Предусловие: {pre}")
    lines.append("Шаги:")

    # Сшиваем действия и ожидаемые результаты по индексу
    max_len = max(len(steps_lines), len(exp_lines))
    for i in range(max_len):
        num = i + 1
        action = steps_lines[i].strip() if i < len(steps_lines) else ""
        expected = exp_lines[i].strip() if i < len(exp_lines) else ""
        if not action and not expected:
            continue
        lines.append(f"{num}) {action or 'Шаг без описания'}")
        if expected:
            lines.append(f"   ОР: {expected}")

    return "\n".join(lines) + "\n"


def main():
    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Файл с тестами не найден: {EXCEL_PATH}")

    print(f"[AQA] Читаю Excel: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)

    # Для наглядности — выведем кол-во строк
    print(f"[AQA] Найдено строк: {len(df)}")

    imported = 0
    for idx, row in df.iterrows():
        markdown = row_to_markdown(row)
        print(f"\n[AQA] ---- Тест {idx + 1} ----")
        print(markdown)

        result = push_to_qase(markdown)
        print("[AQA] Результат отправки:", result)

        if result.get("status") in ("ok", "mock"):
            imported += 1

    print(f"\n[AQA] Импорт завершён. Успешно обработано тестов: {imported}/{len(df)}")


if __name__ == "__main__":
    main()
