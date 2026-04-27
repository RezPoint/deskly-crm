# Дизайн: 4 новые фичи deskly-crm

**Дата:** 2026-04-06  
**Контекст:** CRM для малого бизнеса в РФ, несколько пользователей, tenant_id=1

---

## Фича 1: Страница настроек + PDF счёт на оплату

### Цель
Владелец вводит реквизиты один раз → скачивает счёт по любому заказу.

### БД — новая таблица `tenant_settings`
- company, inn, kpp, ogrn, address, bank, bik, rs, ks

### Backend
- GET/PUT /api/v1/settings
- GET /api/v1/orders/{id}/invoice → PDF (gofpdf)

### Frontend
- Страница /settings с формой реквизитов
- Кнопка "Скачать счёт" на заказе

---

## Фича 2: Канбан

### Backend
Без изменений — PATCH /api/v1/orders/{id}/status уже есть.

### Frontend
- Страница /kanban, библиотека @dnd-kit/core
- 4 колонки: Новый / В работе / Готов / Отменён
- Карточка: клиент, заголовок, сумма, долг, бейдж дедлайна
- Оптимистичный UI update при drag

---

## Фича 3: Дедлайны для заказов

### БД
- Добавить due_date *time.Time в orders

### Backend
- Dashboard stats добавить overdue_count, due_today_count

### Frontend
- Поле даты в форме заказа
- Бейджи: красный "Просрочен" / жёлтый "Сегодня" / серый с датой
- 2 новых карточки на дашборде

---

## Фича 4: Публичная ссылка

### БД
- Добавить public_token string(36) в orders

### Backend
- POST /api/v1/orders/{id}/share → генерирует UUID
- GET /api/v1/public/orders/{token} — без JWT, ограниченные данные

### Frontend
- Кнопка "Поделиться" → копирует ссылку
- Страница /p/:token — публичный view для клиента

---

## Порядок реализации
1. Дедлайны (только БД + UI)
2. Публичная ссылка
3. Канбан
4. Настройки + PDF

## Затронутые файлы
- internal/domain/models.go — Order + TenantSettings
- internal/db/db.go — AutoMigrate
- cmd/server/main.go — новые роуты
- internal/handler/ — settings, invoice, public handlers
- go.mod — добавить gofpdf
- src/pages/ — Settings, Kanban, PublicOrder
- src/hooks/useSettings.ts
- src/types/index.ts
- src/components/Layout.tsx — sidebar
- src/pages/Dashboard.tsx, Orders.tsx
- package.json — @dnd-kit
