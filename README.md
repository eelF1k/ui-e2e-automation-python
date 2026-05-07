# UI E2E Automation (Python)

## Назва проєкту
UI E2E Automation (Python)

## Це мій пет проєкт про...
Це мій пет проєкт про E2E UI автоматизацію вебзастосунку на Python з Selenium та Pytest.

## Технологічний стек
- Python
- Pytest
- Selenium WebDriver
- GitHub Actions

## Що реалізовано
- UI тести для авторизації та базового checkout flow.
- Патерн Page Object Model.
- Smoke та regression запуск через pytest markers.
- Збір артефактів падінь (screenshot/page source).
- CI запуск тестів у GitHub Actions.

## Структура
- `tests/` — UI тести
- `docs/` — тестова документація
- `configs/` — pytest конфігурація
- `reports/` — артефакти падінь

## Архітектура
- Тести викликають сторінкові об'єкти.
- Сторінкові об'єкти інкапсулюють локатори та дії.
- Фікстури керують браузером і параметрами запуску.

## Що потрібно встановити для тесту
- Python 3.12+
- Google Chrome

## Як запустити
```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
$env:PYTHONPATH="."
pytest --base-url https://www.saucedemo.com --headless
```

