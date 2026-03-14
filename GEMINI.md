# Проект DesklyCRM: Менеджер клиентов и заказов

DesklyCRM — это высокопроизводительная CRM-система, полностью переписанная на Go и React в марте 2026 года.

## Архитектура и технологии (Обновлено)

- **Язык**: Go 1.22+ (Backend), TypeScript (Frontend).
- **Backend**: Стандартная библиотека Go (`http.NewServeMux`), GORM (ORM), JWT для аутентификации.
- **Frontend**: React + Vite, Tailwind-like Vanilla CSS (Glassmorphism), Lucide-React.
- **База данных**: SQLite.
- **Структура**: Clean Architecture (Domain -> Repository -> Service -> Handler).

## Структура проекта (Новая)

- `go-backend/cmd/server/main.go`: Точка входа, конфигурация роутов и раздача статики.
- `go-backend/internal/domain/`: Модели данных (Entities) с поддержкой Soft Delete и Decimal.
- `go-backend/internal/repository/`: Слой доступа к данным (GORM).
- `go-backend/internal/service/`: Бизнес-логика (расчеты, транзакции).
- `go-backend/internal/handler/`: HTTP-хендлеры и Middleware (CORS).
- `go-backend/frontend/`: Исходный код React-приложения.
- `go-backend/frontend/dist/`: Скомпилированный фронтенд, раздаваемый Go-сервером.

## Роль Gemini CLI

Агент имеет право самостоятельно обновлять этот файл при внесении значимых изменений. 

## Технический аудит (Март 2026)

### Проведенные работы (Full Rewrite):
1. **Миграция на Go**: Весь бэкенд переписан с FastAPI на Golang для повышения стабильности и скорости.
2. **React SPA**: Старый Vanilla JS заменен на современный React с типизацией.
3. **Финансовый блок**: Реализована система платежей с автоматическим пересчетом выручки и оборота.
4. **Умный UX**: Внедрен Searchable Select для клиентов и встроенные модальные окна подтверждения вместо браузерных.
5. **SPA Routing**: Настроена корректная обработка F5 (все не-API запросы ведут на index.html).

## Инструкции для работы

### Запуск сервера
`cd go-backend && go run ./cmd/server/main.go`

### Разработка фронтенда
При изменении фронтенда обязательно выполнять `npm run build` внутри `go-backend/frontend`, чтобы Go-сервер увидел обновления.

### Стиль кода
1. **Go**: Строгая проверка ошибок `if err != nil`. Использование интерфейсов для репозиториев.
2. **Frontend**: Функциональные компоненты React, строгий TypeScript.
