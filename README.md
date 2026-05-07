## UI E2E Automation (Python)

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

### Запуск тестів (поки що)
На наступних кроках тут з’являться UI-тести та команди запуску через `pytest`.

### Структура (high-level)
- `tests/` — автотести (UI E2E)
- `docs/` — тест-план, матриця покриття, шаблон баг-репорту
- `configs/` — конфіги (pytest тощо)
- `reports/` — артефакти запусків (локально/CI), не комітяться

### Статус
Репозиторій ініціалізовано. Далі — поетапне додавання інфраструктури Selenium/pytest і тестів окремими комітами.

