# CRM Features Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Добавить 4 фичи: дедлайны, публичная ссылка, канбан, настройки + PDF счёт на оплату.
**Tech Stack:** Go 1.22+, GORM, SQLite, React 18, TypeScript, @dnd-kit/core, github.com/go-pdf/fpdf

---

## FEATURE 1: Дедлайны для заказов

### Task 1: Модели + AutoMigrate

**Files:** `go-backend/internal/domain/models.go`, `go-backend/internal/db/db.go`

- [ ] **Step 1: Обновить Order — добавить DueDate, PublicToken; добавить TenantSettings**

Заменить структуру Order в `go-backend/internal/domain/models.go`:

```go
type Order struct {
	BaseEntity
	ClientID    uint            `gorm:"not null" json:"client_id"`
	Title       string          `gorm:"size:200;not null" json:"title"`
	Price       decimal.Decimal `gorm:"type:numeric(12,2);not null;default:0" json:"price"`
	Status      string          `gorm:"size:30;not null;default:'new'" json:"status"`
	Comment     string          `gorm:"type:text" json:"comment"`
	DueDate     *time.Time      `gorm:"index" json:"due_date"`
	PublicToken *string         `gorm:"size:36;uniqueIndex" json:"public_token,omitempty"`
	Items    []OrderItem `gorm:"foreignKey:OrderID" json:"items,omitempty"`
	Payments []Payment   `gorm:"foreignKey:OrderID" json:"payments,omitempty"`
}
```

Добавить в конец файла:

```go
type TenantSettings struct {
	ID       uint   `gorm:"primaryKey" json:"id"`
	TenantID uint   `gorm:"not null;uniqueIndex" json:"tenant_id"`
	Company  string `gorm:"size:200" json:"company"`
	INN      string `gorm:"size:20" json:"inn"`
	KPP      string `gorm:"size:20" json:"kpp"`
	OGRN     string `gorm:"size:20" json:"ogrn"`
	Address  string `gorm:"size:500" json:"address"`
	Bank     string `gorm:"size:200" json:"bank"`
	BIK      string `gorm:"size:20" json:"bik"`
	RS       string `gorm:"size:30" json:"rs"`
	KS       string `gorm:"size:30" json:"ks"`
}
```

- [ ] **Step 2:** В `go-backend/internal/db/db.go` добавить `&domain.TenantSettings{}` в `db.AutoMigrate(...)`.

- [ ] **Step 3:** `cd /c/github/deskly-crm/go-backend && go build ./cmd/server/main.go`

- [ ] **Step 4:** `git add go-backend/internal/domain/models.go go-backend/internal/db/db.go && git commit -m "feat(models): add due_date, public_token to Order; add TenantSettings"`

### Task 2: Dashboard stats

**Files:** `go-backend/internal/handler/dashboard_handler.go`

- [ ] **Step 1:** В `GetStats` после строки `activeTasks` добавить:

```go
var overdueCount int64
var dueTodayCount int64
h.db.Model(&domain.Order{}).
	Where("tenant_id=? AND status NOT IN (?,?) AND due_date < date('now') AND due_date IS NOT NULL", 1,"done","cancelled").
	Count(&overdueCount)
h.db.Model(&domain.Order{}).
	Where("tenant_id=? AND status NOT IN (?,?) AND date(due_date)=date('now') AND due_date IS NOT NULL", 1,"done","cancelled").
	Count(&dueTodayCount)
```

- [ ] **Step 2:** В map `stats` добавить `"overdue_count": overdueCount, "due_today_count": dueTodayCount`

- [ ] **Step 3:** `go build ./cmd/server/main.go && git add go-backend/internal/handler/dashboard_handler.go && git commit -m "feat(dashboard): add overdue_count and due_today_count"`

### Task 3: TypeScript типы

**Files:** `go-backend/frontend/src/types/index.ts`

- [ ] **Step 1:** Обновить `Order` — добавить `due_date?: string | null` и `public_token?: string | null`

- [ ] **Step 2:** Обновить `DashboardStats` — добавить `overdue_count: number` и `due_today_count: number`

- [ ] **Step 3:** Добавить в конец файла:
```typescript
export interface TenantSettings {
  company: string; inn: string; kpp: string; ogrn: string;
  address: string; bank: string; bik: string; rs: string; ks: string;
}
```

- [ ] **Step 4:** `git add go-backend/frontend/src/types/index.ts && git commit -m "feat(types): update Order, DashboardStats; add TenantSettings"`

### Task 4: UI дедлайнов

**Files:** `go-backend/frontend/src/hooks/useOrders.ts`, `go-backend/frontend/src/pages/Orders.tsx`, `go-backend/frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1:** В `useOrders.ts` добавить `due_date?: string | null` в тип payload функции `create`

- [ ] **Step 2:** В `Orders.tsx` после импортов добавить компонент:
```tsx
function DueDateBadge({ dueDate }: { dueDate?: string | null }) {
  if (!dueDate) return null;
  const today = new Date().toISOString().slice(0, 10);
  const due = dueDate.slice(0, 10);
  if (due < today) return <span className="ml-2 px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-400 border border-red-500/30">Просрочен</span>;
  if (due === today) return <span className="ml-2 px-2 py-0.5 rounded-full text-xs bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">Сегодня</span>;
  return <span className="ml-2 px-2 py-0.5 rounded-full text-xs bg-white/10 text-gray-400">{due}</span>;
}
```

- [ ] **Step 3:** В форме заказа добавить:
```tsx
<div>
  <label className="block text-sm font-medium text-gray-300 mb-1">Срок выполнения</label>
  <input type="date" value={formData.due_date ?? ''}
    onChange={e => setFormData(prev => ({ ...prev, due_date: e.target.value || null }))}
    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white" />
</div>
```

- [ ] **Step 4:** Рядом с title заказа в списке добавить `<DueDateBadge dueDate={order.due_date} />`

- [ ] **Step 5:** В `Dashboard.tsx` в сетку карточек добавить:
```tsx
{stats.overdue_count > 0 && (
  <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
    <div className="text-2xl font-bold text-red-400">{stats.overdue_count}</div>
    <div className="text-sm text-red-300 mt-1">Просроченных заказов</div>
  </div>
)}
{stats.due_today_count > 0 && (
  <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4">
    <div className="text-2xl font-bold text-yellow-400">{stats.due_today_count}</div>
    <div className="text-sm text-yellow-300 mt-1">Срок сегодня</div>
  </div>
)}
```

- [ ] **Step 6:** `npm run build && git add go-backend/frontend/src/pages/Orders.tsx go-backend/frontend/src/hooks/useOrders.ts go-backend/frontend/src/pages/Dashboard.tsx && git commit -m "feat(orders): due_date field, deadline badges; feat(dashboard): overdue cards"`

---

## FEATURE 2 (continued)

### Task 6: PublicOrder страница + кнопка Поделиться

См. код в specs файле. Ключевые шаги:

- [ ] Создать `go-backend/frontend/src/pages/PublicOrder.tsx` (страница публичного просмотра заказа без авторизации)
- [ ] В App.tsx добавить вне Layout: `<Route path="/p/:token" element={<PublicOrder />} />`
- [ ] В Orders.tsx добавить кнопку Share2 и функцию handleShare
- [ ] `npm run build && git commit -m "feat(public): public order page and share button"`

---

## FEATURE 3: Канбан

### Task 7: Kanban страница

**Files:** Create `go-backend/frontend/src/pages/Kanban.tsx`, Modify `App.tsx`, `Layout.tsx`

- [ ] **Step 1:** `cd /c/github/deskly-crm/go-backend/frontend && npm install @dnd-kit/core @dnd-kit/utilities`

- [ ] **Step 2:** Создать `go-backend/frontend/src/pages/Kanban.tsx` с 4 колонками (new/in_work/done/cancelled), drag-and-drop через @dnd-kit, оптимистичным обновлением через PATCH /orders/{id}/status

- [ ] **Step 3:** В App.tsx добавить: `import Kanban from "./pages/Kanban"` и `<Route path="/kanban" element={<Kanban />} />`

- [ ] **Step 4:** В Layout.tsx добавить `LayoutGrid` из lucide-react и пункт `{ path: "/kanban", label: "Канбан", icon: LayoutGrid }`

- [ ] **Step 5:** `npm run build && git add ... && git commit -m "feat(kanban): kanban board with drag-and-drop"`

---

## FEATURE 4: Настройки + PDF счёт

### Task 8: Settings handler

**Files:** Create `go-backend/internal/handler/settings_handler.go`, Modify `go-backend/cmd/server/main.go`

- [ ] Создать SettingsHandler с методами GetSettings (FirstOrCreate) и UpdateSettings (upsert через clause.OnConflict)
- [ ] Зарегистрировать: `GET /api/v1/settings` и `PUT /api/v1/settings`
- [ ] `go build && git commit -m "feat(settings): GET/PUT /api/v1/settings"`

### Task 9: Settings страница

**Files:** Create `go-backend/frontend/src/hooks/useSettings.ts`, `go-backend/frontend/src/pages/Settings.tsx`, Modify `App.tsx`, `Layout.tsx`

- [ ] Создать useSettings.ts — хук с load/save, состоянием saving/saved
- [ ] Создать Settings.tsx — форма с полями: company, inn, kpp, ogrn, address, bank, bik, rs, ks
- [ ] В App.tsx: `<Route path="/settings" element={<SettingsPage />} />`
- [ ] В Layout.tsx: иконка Settings (алиас SettingsIcon чтобы не конфликтовать с компонентом)
- [ ] `npm run build && git commit -m "feat(settings): settings page with company details form"`

### Task 10: PDF генерация + кнопка скачивания

**Files:** Create `go-backend/internal/handler/invoice_handler.go`, Modify `go-backend/cmd/server/main.go`, `go-backend/frontend/src/pages/Orders.tsx`

- [ ] `cd /c/github/deskly-crm/go-backend && go get github.com/go-pdf/fpdf`
- [ ] Создать InvoiceHandler.GenerateInvoice: загружает заказ+позиции+клиента+реквизиты, генерирует PDF через fpdf, отдаёт как attachment
- [ ] Зарегистрировать: `GET /api/v1/orders/{id}/invoice`
- [ ] В Orders.tsx добавить handleDownloadInvoice (fetch с JWT, blob download) и кнопку FileDown
- [ ] `go build && npm run build && git commit -m "feat(invoice): PDF invoice generation and download button"`

---

## Финальная проверка

- [ ] `cd /c/github/deskly-crm/go-backend && go run ./cmd/server/main.go`
- [ ] В логах: `База данных инициализирована и мигрирована`
- [ ] Dashboard — карточки просрочки при наличии заказов с due_date
- [ ] Заказы — поле даты в форме, бейдж в списке
- [ ] Поделиться — `/p/{token}` открывается без логина
- [ ] `/kanban` — drag and drop меняет статус
- [ ] `/settings` — реквизиты сохраняются
- [ ] Скачать счёт — скачивается PDF
