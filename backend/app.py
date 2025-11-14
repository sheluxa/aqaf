from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    TestCaseRequest,
    AutoTestRequest,
    AutoTestResponse,
)
from services.generation import generate_testcase, generate_playwright
from services.qase_client import push_to_qase

HTML_UI = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8"/>
  <title>AQA Prototype UI</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; padding: 16px; background: #f4f4f8; }
    h1 { margin-top: 0; }
    textarea { width: 100%; min-height: 140px; font-family: monospace; padding: 8px; }
    .row { display: flex; gap: 16px; margin-top: 16px; }
    .col { flex: 1; display: flex; flex-direction: column; }
    pre { background: #111; color: #eee; padding: 8px; overflow: auto; border-radius: 6px; }
    button { padding: 8px 16px; font-size: 14px; cursor: pointer; border-radius: 4px; border: none; background: #2563eb; color: white; }
    button:disabled { opacity: 0.5; cursor: default; }
    .topbar { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
    .status { font-size: 12px; color: #555; }
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 11px; background: #e0e7ff; color: #1d4ed8; }
  </style>
</head>
<body>
  <div class="topbar">
    <h1 style="flex:1">AQA Prototype</h1>
    <span class="badge">Prototype / No real export</span>
  </div>
  <p>Вставь описание кейса (как в Excel/Google Sheets) и нажми «Сгенерировать».</p>

  <textarea id="prompt" placeholder="Например: Авторизация — ввод телефона..."></textarea>
  <div style="margin-top:8px;">
    <label><input type="checkbox" id="push_mock" /> Сохранить mock-файл выгрузки (qase_push_mock.json)</label>
  </div>
  <div style="margin-top:8px;">
    <button id="go">Сгенерировать</button>
    <span id="status" class="status"></span>
  </div>

  <div class="row">
    <div class="col">
      <h3>Сгенерированный тест-кейс</h3>
      <pre id="testcase"></pre>
    </div>
    <div class="col">
      <h3>Сгенерированный Playwright-тест</h3>
      <pre id="code"></pre>
    </div>
  </div>

<script>
const btn = document.getElementById('go');
const promptEl = document.getElementById('prompt');
const statusEl = document.getElementById('status');
const tcEl = document.getElementById('testcase');
const codeEl = document.getElementById('code');
const pushMockEl = document.getElementById('push_mock');

btn.onclick = async () => {
  const prompt = promptEl.value.trim();
  if (!prompt) {
    alert('Введи описание теста');
    return;
  }
  btn.disabled = true;
  statusEl.textContent = 'Генерация...';

  try {
    const resp = await fetch('/generate/full', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        prompt,
        prefer_style: 'concise',
        push_to_qase: pushMockEl.checked
      })
    });
    if (!resp.ok) {
      statusEl.textContent = 'Ошибка: ' + resp.status;
      btn.disabled = false;
      return;
    }
    const data = await resp.json();
    tcEl.textContent = data.testcase || '';
    codeEl.textContent = data.code || '';
    if (data.qase_mock && data.qase_mock.saved_to) {
      statusEl.textContent = 'Готово. Mock-файл: ' + data.qase_mock.saved_to;
    } else {
      statusEl.textContent = 'Готово.';
    }
  } catch (e) {
    console.error(e);
    statusEl.textContent = 'Ошибка: ' + e;
  } finally {
    btn.disabled = false;
  }
};
</script>
</body>
</html>
"""

app = FastAPI(title="AQA Backend MVP")

# --- CORS, чтобы фронт (если появится) мог ходить к API ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- middleware для utf-8 ---
@app.middleware("http")
async def add_charset(request, call_next):
    resp = await call_next(request)
    ct = resp.headers.get("content-type", "")
    if ct.startswith("application/json") and "charset" not in ct.lower():
        resp.headers["content-type"] = "application/json; charset=utf-8"
    return resp


@app.get("/health")
def health():
    return {"status": "ok"}


# 🔹 Новый удобный эндпоинт: сразу и тест-кейс, и код
@app.post("/generate/full")
def generate_full(req: TestCaseRequest):
    """
    Получает prompt → отдаёт текстовый тест-кейс и Playwright-автотест.
    Опционально сохраняет mock-файл "как будто отправили в Qase".
    """
    testcase = generate_testcase(req.prompt, prefer_style=req.prefer_style)
    code = generate_playwright(testcase, base_url="http://localhost:3000")

    qase_result = None
    if req.push_to_qase:
        qase_result = push_to_qase(testcase)

    return {
        "testcase": testcase,
        "code": code,
        "qase_mock": qase_result,
    }


# Старые эндпоинты оставляем для совместимости (Swagger / плагин)

@app.post("/generate/testcase")
def generate_testcase_api(req: TestCaseRequest):
    testcase = generate_testcase(req.prompt, prefer_style=req.prefer_style)
    qase_result = push_to_qase(testcase) if req.push_to_qase else None
    return {"testcase": testcase, "qase_mock": qase_result}


@app.post("/generate/autotest", response_model=AutoTestResponse)
def generate_autotest_api(req: AutoTestRequest):
    code = generate_playwright(req.testcase_text, base_url=req.base_url)
    return AutoTestResponse(code=code)


# 🔹 Простейший веб-UI прямо из FastAPI (без отдельного фронта)
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return HTML_UI
