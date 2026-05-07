## UI E2E Automation (Python)

[![UI E2E CI](https://github.com/eelF1k/ui-e2e-automation-python/actions/workflows/ci.yml/badge.svg)](https://github.com/eelF1k/ui-e2e-automation-python/actions/workflows/ci.yml)

Пет-проєкт для демонстрації навичок **Automation Engineer (Python)**: E2E UI тести на **Selenium + Pytest** з патерном **Page Object Model**, артефактами при падіннях та CI.

### Стек
- Python
- Pytest
- Selenium WebDriver

### Встановлення (Windows / PowerShell)
Створи venv та встанови залежності:

```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

### Запуск тестів
Перед запуском для цього демо-проєкту встанови базову URL:

```bash
$env:PYTHONPATH="."
pytest --base-url https://www.saucedemo.com --headless
```

Корисні варіанти запуску:

```bash
# smoke suite
pytest -m smoke --base-url https://www.saucedemo.com --headless

# regression suite
pytest -m regression --base-url https://www.saucedemo.com --headless

# конкретний файл
pytest tests/ui/test_auth.py --base-url https://www.saucedemo.com --headless
```

### Структура (high-level)
- `tests/` — автотести (UI E2E)
- `docs/` — тест-план, матриця покриття, шаблон баг-репорту
- `configs/` — конфіги (pytest тощо)
- `reports/` — артефакти запусків (локально/CI), не комітяться

### CI
- GitHub Actions workflow: `.github/workflows/ci.yml`
- На кожен `push` / `pull_request` в `master` запускається smoke suite.
- При падіннях CI публікуються артефакти з `reports/ui_failures/`.

### Статус
MVP фреймворк готовий: є Page Objects, smoke/regression сьюти, базовий checkout flow, артефакти падінь і CI.

