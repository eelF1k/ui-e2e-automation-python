## UI E2E Automation (Python)

Це мій пет-проєкт для демонстрації навичок **Automation Engineer (Python)**.
Тут я реалізував E2E UI автотести на **Selenium + Pytest** з патерном **Page Object Model**, артефактами при падіннях і CI.

### Що я використав
- Python
- Pytest
- Selenium WebDriver

### Що я вмію цим проєктом
- Писати E2E UI автотести на Python + Pytest + Selenium.
- Будувати фреймворк з Page Object Model і reusable утилітами.
- Валідувати smoke/regression сценарії для авторизації та checkout flow.
- Налаштовувати CI в GitHub Actions для автоматичного запуску тестів.
- Аналізувати падіння через screenshot/page source артефакти.

### Що потрібно встановити для тесту
- Python 3.12+ (або сумісна версія)
- Google Chrome

### Як запустити локально (Windows / PowerShell)
Зробити це по кроках:

```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

### Запуск тестів
Перед запуском встановити `PYTHONPATH` і передати базову URL:

```bash
$env:PYTHONPATH="."
pytest --base-url https://www.saucedemo.com --headless
```

Ще варіанти запуску:

```bash
# smoke suite
pytest -m smoke --base-url https://www.saucedemo.com --headless

# regression suite
pytest -m regression --base-url https://www.saucedemo.com --headless

# конкретний файл
pytest tests/ui/test_auth.py --base-url https://www.saucedemo.com --headless
```

### Структура (high-level)
- `tests/` — UI E2E автотести
- `docs/` — test plan, matrix, bug report template
- `configs/` — pytest конфіги
- `reports/` — артефакти падінь (локально/CI), не комічу в git

### CI
- GitHub Actions workflow: `.github/workflows/ci.yml`
- На кожен `push` / `pull_request` в `master` запускається smoke suite.
- При падіннях CI публікуються артефакти з `reports/ui_failures/`.

### Статус
MVP фреймворк готовий: є Page Objects, smoke/regression сьюти, базовий checkout flow, артефакти падінь і CI.

