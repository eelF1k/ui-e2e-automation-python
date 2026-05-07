# Test Coverage Matrix

| ID | Feature | Scenario | Type | Priority | Automation | Status |
|---|---|---|---|---|---|---|
| AUTH-001 | Login | Успішний логін валідним користувачем | Smoke | High | Yes | Implemented |
| AUTH-002 | Login | Невірний пароль показує помилку | Smoke | High | Yes | Implemented |
| AUTH-003 | Login | Locked out user отримує помилку | Smoke | High | Yes | Implemented |
| CAT-001 | Catalog | Додати перший товар у кошик | Regression | High | Yes | Implemented |
| CART-001 | Cart | Відкрити кошик і побачити товар | Regression | High | Yes | Implemented |
| CHK-001 | Checkout | Перехід на `checkout-step-one` | Regression | High | Yes | Implemented |
| CHK-002 | Checkout | Заповнити checkout form валідно | Regression | Medium | Planned | Backlog |
| CHK-003 | Checkout | Валідація порожніх полів checkout | Regression | Medium | Planned | Backlog |

## Примітки
- Smoke suite запускається в CI на кожен `push` і `pull_request`.
- Regression suite запускається вручну або за окремим workflow (додати в наступних ітераціях).
- Статуси:
  - **Implemented** — сценарій автоматизовано і комічено в репозиторій.
  - **Planned** — сценарій заплановано, але ще не реалізовано.

