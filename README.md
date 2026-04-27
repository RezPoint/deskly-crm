# DesklyCRM

Лёгкая CRM для малого бизнеса: клиенты, заказы, товары, задачи, платежи. Бэкенд на Go + GORM, фронтенд на React + TypeScript, локальная база SQLite. Один бинарник, который раздаёт собранный SPA — ставится на VPS или запускается локально.

## Возможности

- **Клиенты** — карточка с телефоном, телеграмом, заметками; история заказов.
- **Заказы** — позиции (`OrderItem`), статусы, частичные оплаты через `Payment`, авто-расчёт итоговой суммы.
- **Товары/услуги** — каталог с ценами, флагом активности, soft-delete.
- **Задачи** — привязка к клиенту/заказу, дедлайн, статусы.
- **Платежи** — учёт частичных оплат с пересчётом остатка по заказу.
- **Дашборд** — оборот, выручка, число клиентов, последние действия (`ActivityLog`).
- **Авторизация** — JWT, хеш паролей, multi-tenant (`tenant_id` на каждой сущности).
- **Темы** — light / dark, переключение с сохранением в localStorage.
- **Адаптивность** — sidebar превращается в overlay на ширине < 768px, таблицы со скроллом.

## Стек

**Backend** (Go 1.22+):
- `gorm.io/gorm` + SQLite драйвер
- `github.com/shopspring/decimal` для денежных полей
- `golang-jwt/jwt` для токенов
- стандартный `net/http` без фреймворка

**Frontend** (Node 20+):
- React 18 + TypeScript
- Vite (dev/build)
- Lucide-React (иконки)
- React Router

## Архитектура

```
go-backend/
  cmd/server/main.go          инициализация, регистрация хендлеров, http.ListenAndServe
  internal/
    domain/models.go          GORM-модели: Tenant, User, Client, Order/OrderItem/Payment,
                              Product, Task, OrderComment, ActivityLog
    db/db.go                  InitDB, AutoMigrate, seed дефолтного юзера
    repository/               CRUD на уровне БД (один файл на сущность)
    service/                  бизнес-логика
    handler/                  HTTP-эндпоинты + middleware (JWT, tenant)
  frontend/
    src/
      pages/                  Dashboard, Clients, ClientDetail, Orders, Products, Tasks, Login
      components/             Sidebar, Modal, ConfirmDialog, ...
      api/client.ts           обёртка над fetch с JWT
      hooks/, types/, styles/

# Старый Python/FastAPI бэкенд (в процессе удаления):
app/, alembic/, requirements.txt, pyproject.toml
```

В марте 2026 проект переписан с Python/FastAPI на Go + React. Старый код временно оставлен в репозитории до полной верификации фич — в сборку не входит.

## Запуск

### Production (один бинарник)

```bash
cd go-backend
cd frontend && npm install && npm run build && cd ..
go build -o deskly_server ./cmd/server
./deskly_server
```

Открыть `http://localhost:8080`. Бэкенд раздаёт `frontend/dist` как статику.

Дефолтный логин при первом запуске:

- email: `admin@deskly.com`
- password: `password`

После входа — сменить пароль.

### Разработка фронтенда

```bash
cd go-backend
go run ./cmd/server/main.go      # бэкенд на :8080

# в другом терминале
cd go-backend/frontend
npm install
npm run dev                       # Vite dev-server на :5173
```

## Конфигурация (переменные окружения)

| Переменная | Описание | По умолчанию |
|---|---|---|
| `JWT_SECRET` | Секрет для подписи JWT | `super_secret_key_123` (только для разработки!) |
| `DB_PATH` | Путь к SQLite-файлу | `deskly.db` |
| `STATIC_DIR` | Папка с собранным фронтом | `frontend/dist` |
| `PORT` | Порт HTTP-сервера | `8080` |

**Перед деплоем `JWT_SECRET` обязательно задать.** В логах будет предупреждение, если переменная не установлена.

## База данных

SQLite, одна файловая БД (`deskly.db`). Миграции — `AutoMigrate` от GORM при старте. Денежные поля — `decimal.Decimal` через `numeric(12,2)`, чтобы избежать float-погрешностей.

Soft-delete (`gorm.DeletedAt`) включён на всех сущностях, кроме `Tenant`.

## Multi-tenancy

Все бизнес-сущности наследуют `BaseEntity` с обязательным `TenantID` и индексом по нему. Middleware извлекает `tenant_id` из JWT и подставляет в запросы — данные одного арендатора изолированы от других на уровне репозиториев.

## Лицензия

MIT — см. [LICENSE](LICENSE).
