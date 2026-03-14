// DesklyCRM Frontend Vanilla JS Application
const API_BASE = '/api/v1';

// Global state
const state = {
    token: localStorage.getItem('access_token') || null,
    user: null,
    currentView: 'login', // 'login', 'clients', 'orders'
    taskViewMode: 'table' // 'table', 'kanban'
};

// Elements
const el = {
    viewLogin: document.getElementById('view-login'),
    viewDashboard: document.getElementById('view-dashboard'),
    formLogin: document.getElementById('form-login'),
    btnLogout: document.getElementById('btn-logout'),
    navItems: document.querySelectorAll('.nav-item'),
    pageTitle: document.getElementById('page-title'),
    pageSubtitle: document.getElementById('page-subtitle'),
    pageActions: document.getElementById('page-actions'),
    tableHead: document.getElementById('data-table-head'),
    tableBody: document.getElementById('data-table-body'),
    tableToolbar: document.getElementById('table-toolbar'),
    emptyState: document.getElementById('empty-state'),
    toastContainer: document.getElementById('toast-container'),
    modalContainer: document.getElementById('modal-container'),
    dynamicModal: document.getElementById('dynamic-modal'),
    tableContainer: document.getElementById('table-container'),
    dashboardContent: document.getElementById('dashboard-content'),
    btnTheme: document.getElementById('btn-theme'),
    themeLabel: document.getElementById('theme-label'),
    themeIconSun: document.getElementById('theme-icon-sun'),
    themeIconMoon: document.getElementById('theme-icon-moon'),
    btnHamburger: document.getElementById('btn-hamburger'),
    sidebar: document.getElementById('sidebar'),
    sidebarOverlay: document.getElementById('sidebar-overlay'),
    viewKanban: document.getElementById('kanban-view'),
    kanbanContainer: document.getElementById('kanban-container'),
};

// --- Initialization ---
async function init() {
    if (state.token) {
        try {
            const res = await apiGet('/auth/me');
            state.user = res;
            switchView('dashboard');
            updateUserInfo();
        } catch (e) {
            handleLogout();
        }
    } else {
        switchView('login');
    }
}

// --- Navigation & View Control ---
function switchView(target) {
    state.currentView = target;

    if (target === 'login') {
        el.viewDashboard.classList.remove('active');
        el.viewLogin.classList.add('active');
    } else {
        el.viewLogin.classList.remove('active');
        el.viewDashboard.classList.add('active');

        // Update Nav Menu active state
        el.navItems.forEach(item => {
            if (item.dataset.target === target) item.classList.add('active');
            else item.classList.remove('active');
        });

        // Toggle containers
        el.viewKanban.style.display = 'none'; // Ensure Kanban is hidden by default
        if (target === 'dashboard') {
            el.tableContainer.style.display = 'none';
            el.dashboardContent.style.display = 'block';
            loadDashboard();
        } else {
            el.tableContainer.style.display = 'block';
            el.dashboardContent.style.display = 'none';
            if (target === 'clients') loadClients();
            else if (target === 'orders') loadOrders();
            else if (target === 'catalog') loadCatalog();
            else if (target === 'activity') loadActivity();
            else if (target === 'reminders') loadTasks();
            else if (target === 'settings') loadSettings();
        }
    }
}

function updateUserInfo() {
    if (state.user) {
        document.getElementById('current-user-email').textContent = state.user.email;
        document.getElementById('current-user-role').textContent = state.user.role;
    }
}

// --- Event Listeners ---
el.navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        switchView(item.dataset.target);
    });
});

el.formLogin.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const res = await apiPost('/auth/login', { email, password });
        state.token = res.access_token;
        localStorage.setItem('access_token', res.access_token);
        const userRes = await apiGet('/auth/me');
        state.user = userRes;
        updateUserInfo();
        showToast('Успешный вход', 'success');
        switchView('clients');
    } catch (err) {
        console.error(err);
        showToast('Ошибка входа. Проверьте почту и пароль.', 'error');
    }
});

el.btnLogout.addEventListener('click', async () => {
    await handleLogout();
});

// --- Theme Toggle ---
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    if (theme === 'dark') {
        el.themeIconSun.style.display = 'none';
        el.themeIconMoon.style.display = 'block';
        el.themeLabel.textContent = 'Светлая тема';
    } else {
        el.themeIconSun.style.display = 'block';
        el.themeIconMoon.style.display = 'none';
        el.themeLabel.textContent = 'Тёмная тема';
    }
}

// Restore saved theme
const savedTheme = localStorage.getItem('theme') || 'light';
applyTheme(savedTheme);

el.btnTheme.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
});

// --- Mobile Hamburger Menu ---
function openSidebar() {
    el.sidebar.classList.add('open');
    el.sidebarOverlay.classList.add('active');
}

function closeSidebar() {
    el.sidebar.classList.remove('open');
    el.sidebarOverlay.classList.remove('active');
}

el.btnHamburger.addEventListener('click', () => {
    el.sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
});

el.sidebarOverlay.addEventListener('click', closeSidebar);

// Close sidebar on nav click (mobile)
el.navItems.forEach(item => {
    item.addEventListener('click', () => closeSidebar());
});

async function handleLogout() {
    try {
        await apiPost('/auth/logout');
    } catch (e) { }
    state.token = null;
    state.user = null;
    localStorage.removeItem('access_token');
    showToast('Вы вышли из системы', 'success');
    switchView('login');
}

// --- Dashboard Module ---
async function loadDashboard() {
    el.pageTitle.textContent = "Дашборд";
    el.pageSubtitle.textContent = "Сводка показателей";
    el.pageActions.innerHTML = "";
    el.dashboardContent.innerHTML = "<p>Загрузка аналитики...</p>";

    try {
        const data = await apiGet('/analytics/summary');
        renderDashboard(data);
    } catch (e) {
        el.dashboardContent.innerHTML = `<p class="text-danger">Ошибка загрузки дашборда: ${escapeHtml(e.message)}</p>`;
    }
}

function renderDashboard(data) {
    const {
        total_clients, total_orders, active_orders,
        total_revenue, total_debt, recent_activity
    } = data;

    el.dashboardContent.innerHTML = `
        <div class="dashboard-grid" style="gap: 1.5rem; margin-bottom: 2rem;">
            <!-- Total Revenue Card -->
            <div class="glass-panel" style="padding: 1.5rem;">
                <h3 class="text-muted text-sm" style="margin-bottom: 0.5rem; text-transform: uppercase;">Объем заказов</h3>
                <div style="font-size: 2rem; font-weight: 700;">${formatMoney(total_revenue)} ₽</div>
            </div>

            <!-- Paid Card -->
            <div class="glass-panel" style="padding: 1.5rem;">
                <h3 class="text-muted text-sm" style="margin-bottom: 0.5rem; text-transform: uppercase;">Оплачено</h3>
                <div style="font-size: 2rem; font-weight: 700; color: var(--success);">${formatMoney(data.total_paid || 0)} ₽</div>
            </div>
            
            <!-- Debt Card -->
            <div class="glass-panel" style="padding: 1.5rem;">
                <h3 class="text-muted text-sm" style="margin-bottom: 0.5rem; text-transform: uppercase;">Долг клиентов</h3>
                <div style="font-size: 2rem; font-weight: 700; color: ${total_debt > 0 ? 'var(--danger)' : 'var(--text-main)'};">${formatMoney(total_debt)} ₽</div>
            </div>

            <!-- Active Orders Card -->
            <div class="glass-panel" style="padding: 1.5rem;">
                <h3 class="text-muted text-sm" style="margin-bottom: 0.5rem; text-transform: uppercase;">Заказы в работе</h3>
                <div style="font-size: 2rem; font-weight: 700;">${active_orders} <span style="font-size: 1rem; color: var(--text-muted); font-weight: 500;">/ ${total_orders} всего</span></div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr; gap: 1.5rem;">
            <div class="glass-panel" style="padding: 1.5rem;">
                <h3 style="margin-bottom: 1rem; font-weight: 600;">Недавняя активность</h3>
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    ${recent_activity.length === 0 ? '<p class="text-muted">Нет недавних действий</p>' :
            recent_activity.map(act => `
                        <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border);">
                            <div>
                                <div style="font-weight: 500;">${escapeHtml(act.title)}</div>
                                <div class="text-muted text-sm">${escapeHtml(act.message)}</div>
                            </div>
                            <div class="text-muted text-sm">${escapeHtml(act.time)}</div>
                        </div>
                        `).join('')
        }
                </div>
            </div>
        </div>
    `;
}

// --- Clients Module ---
async function loadClients() {
    el.pageTitle.textContent = "Клиенты";
    el.pageSubtitle.textContent = "Ваша клиентская база";

    el.pageActions.innerHTML = `
        <button class="btn btn-primary" onclick="openCreateClientModal()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            Добавить клиента
        </button>
    `;

    try {
        const clients = await apiGet('/clients');
        renderClientsTable(clients);
    } catch (e) {
        showToast('Ошибка загрузки клиентов', 'error');
    }
}

function renderClientsTable(clients) {
    el.tableHead.innerHTML = `
        <tr>
            <th>ID</th>
            <th>Имя</th>
            <th>Контакты</th>
            <th>Заметки</th>
            <th>Действия</th>
        </tr>
    `;

    if (clients.length === 0) {
        el.tableBody.innerHTML = '';
        el.emptyState.style.display = 'block';
    } else {
        el.emptyState.style.display = 'none';
        el.tableBody.innerHTML = clients.map(c => `
            <tr>
                <td class="text-muted">#${c.id}</td>
                <td class="fw-600">${escapeHtml(c.name)}</td>
                <td>
                    ${c.phone ? `<span class="badge new mb-1">${escapeHtml(c.phone)}</span><br>` : ''}
                    ${c.telegram ? `<span class="badge in_progress">${escapeHtml(c.telegram)}</span>` : ''}
                </td>
                <td class="text-sm text-muted">${escapeHtml(c.notes || '-')}</td>
                <td class="actions">
                    <button class="btn btn-sm btn-outline btn-danger" onclick="deleteClient(${c.id})">Удалить</button>
                </td>
            </tr>
        `).join('');
    }
}

function openCreateClientModal() {
    showModal(`
        <div class="modal-header">
            <h3>Новый клиент</h3>
            <button class="btn-close" onclick="closeModal()"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>
        </div>
        <form id="form-create-client" onsubmit="handleCreateClient(event)">
            <div class="input-group">
                <label>Имя клиента</label>
                <input type="text" id="client-name" required>
            </div>
            <div class="input-group">
                <label>Телефон (Опционально)</label>
                <input type="tel" id="client-phone">
            </div>
            <div class="input-group">
                <label>Telegram (Опционально)</label>
                <input type="text" id="client-tg" placeholder="@username">
            </div>
            <div class="input-group">
                <label>Заметки (Опционально)</label>
                <textarea id="client-notes" rows="2"></textarea>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;">
                <button type="button" class="btn btn-outline" onclick="closeModal()">Отмена</button>
                <button type="submit" class="btn btn-primary">Создать</button>
            </div>
        </form>
    `);
}

async function handleCreateClient(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('client-name').value,
        phone: document.getElementById('client-phone').value || null,
        telegram: document.getElementById('client-tg').value || null,
        notes: document.getElementById('client-notes').value || null,
    };

    try {
        await apiPost('/clients', payload);
        closeModal();
        showToast('Клиент успешно создан', 'success');
        loadClients();
    } catch (err) {
        showToast(err.message || 'Ошибка создания', 'error');
    }
}

async function deleteClient(id) {
    if (!confirm('Вы уверены, что хотите удалить клиента и все его заказы?')) return;
    try {
        await apiDelete(`/clients/${id}`);
        showToast('Клиент удален', 'success');
        loadClients();
    } catch (e) {
        showToast('Ошибка удаления', 'error');
    }
}


// --- Orders Module ---
let cachedClients = [];
let cachedProducts = [];
async function loadOrders() {
    el.pageTitle.textContent = "Заказы";
    el.pageSubtitle.textContent = "Текущие проекты и сделки";

    el.pageActions.innerHTML = `
        <button class="btn btn-primary" onclick="openCreateOrderModal()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            Создать заказ
        </button>
    `;

    try {
        const [orders, clients, products] = await Promise.all([
            apiGet('/orders'),
            apiGet('/clients'),
            apiGet('/products').catch(() => [])
        ]);
        cachedClients = clients;
        cachedProducts = products;
        renderOrdersTable(orders);
    } catch (e) {
        showToast('Ошибка загрузки заказов', 'error');
    }
}

function renderOrdersTable(orders) {
    el.tableHead.innerHTML = `
        <tr>
            <th>ID</th>
            <th>Название</th>
            <th>Клиент</th>
            <th>Статус</th>
            <th>Цена</th>
            <th>Действия</th>
        </tr>
            `;

    if (orders.length === 0) {
        el.tableBody.innerHTML = '';
        el.emptyState.style.display = 'block';
    } else {
        el.emptyState.style.display = 'none';

        const clientMap = {};
        cachedClients.forEach(c => clientMap[c.id] = c.name);

        el.tableBody.innerHTML = orders.map(o => `
            <tr>
                <td class="text-muted">#${o.id}</td>
                <td class="fw-600">${escapeHtml(o.title)}</td>
                <td>${escapeHtml(clientMap[o.client_id] || 'Неизвестно')}</td>
                <td><span class="badge ${o.status}">${translateStatus(o.status)}</span></td>
                <td>${formatMoney(o.price)} ₽</td>
                <td class="actions">
                    <button class="btn btn-sm btn-outline" onclick="viewOrder(${o.id})">Подробнее</button>
                    <button class="btn btn-sm btn-outline btn-danger" onclick="deleteOrder(${o.id})">Удалить</button>
                </td>
            </tr>
            `).join('');
    }
}

function openCreateOrderModal() {
    const clientOptions = cachedClients.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');

    if (!clientOptions) {
        showToast('Сначала создайте хотя бы одного клиента', 'error');
        return switchView('clients');
    }

    showModal(`
        <div class="modal-header">
            <h3>Новый заказ</h3>
            <button class="btn-close" onclick="closeModal()">×</button>
        </div>
        <form id="form-create-order" onsubmit="handleCreateOrder(event)">
            <div class="input-group">
                <label>Клиент</label>
                <select id="order-client" required>
                    ${clientOptions}
                </select>
            </div>
            <div class="input-group">
                <label>Название заказа</label>
                <input type="text" id="order-title" required>
            </div>
            
            <div class="input-group">
                <label style="display:flex; justify-content:space-between; align-items:center;">
                    <span>Позиции заказа</span>
                    <button type="button" class="btn btn-outline" onclick="addOrderItemRow()" style="padding: 0.2rem 0.6rem; font-size: 0.8rem;">+ Добавить позицию</button>
                </label>
                <div id="order-items-container" style="display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem;">
                </div>
            </div>

            <div class="input-group" style="margin-top: 1rem;">
                <label>Итоговая стоимость (₽)</label>
                <input type="number" id="order-price" step="0.01" min="0" value="0.00" readonly style="background: var(--bg-body); cursor: not-allowed;">
                <small class="text-muted" style="display:block; margin-top: 0.25rem;">Рассчитывается автоматически</small>
            </div>
            <div class="input-group">
                <label>Комментарий</label>
                <textarea id="order-comment" rows="2"></textarea>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;">
                <button type="button" class="btn btn-outline" onclick="closeModal()">Отмена</button>
                <button type="submit" class="btn btn-primary">Создать</button>
            </div>
        </form>
    `);

    setTimeout(() => {
        addOrderItemRow();
    }, 10);
}

function addOrderItemRow() {
    const container = document.getElementById('order-items-container');
    if (!container) return;

    const rowId = 'oi-' + Date.now() + Math.floor(Math.random() * 1000);

    // Build product options for the dropdown
    const productOpts = cachedProducts
        .filter(p => p.is_active)
        .map(p => `<option value="${p.id}" data-name="${escapeHtml(p.name)}" data-price="${p.price}">${escapeHtml(p.name)} — ${formatMoney(p.price)} ₽</option>`)
        .join('');

    const html = `
        <div class="order-item-row" id="${rowId}" style="display: flex; flex-direction: column; gap: 0.35rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border);">
            <div style="display: flex; gap: 0.5rem; align-items: center;">
                <select class="oi-catalog" style="flex:2; padding:0.4rem;" onchange="fillFromCatalog(this, '${rowId}')">
                    <option value="">— Из каталога —</option>
                    ${productOpts}
                </select>
                <button type="button" class="btn-close" style="color: var(--danger); font-size: 1.2rem; cursor: pointer; padding: 0 0.25rem;" onclick="document.getElementById('${rowId}').remove(); recalcOrderTotal();">×</button>
            </div>
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 0.5rem; align-items: center;">
                <input type="text" class="oi-title" placeholder="Услуга/товар" required>
                <input type="number" class="oi-qty" value="1" min="0.01" step="0.01" placeholder="Кол-во" required oninput="recalcOrderTotal()">
                <input type="number" class="oi-price" value="0.00" min="0" step="0.01" placeholder="Цена" required oninput="recalcOrderTotal()">
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', html);
    recalcOrderTotal();
}

function fillFromCatalog(selectEl, rowId) {
    const row = document.getElementById(rowId);
    if (!row) return;
    const opt = selectEl.options[selectEl.selectedIndex];
    if (!opt || !opt.value) return;
    row.querySelector('.oi-title').value = opt.dataset.name;
    row.querySelector('.oi-price').value = parseFloat(opt.dataset.price).toFixed(2);
    recalcOrderTotal();
}

function recalcOrderTotal() {
    const rows = document.querySelectorAll('.order-item-row');
    let total = 0;
    rows.forEach(row => {
        const qty = parseFloat(row.querySelector('.oi-qty').value) || 0;
        const price = parseFloat(row.querySelector('.oi-price').value) || 0;
        total += (qty * price);
    });
    const priceInput = document.getElementById('order-price');
    if (priceInput) {
        priceInput.value = total.toFixed(2);
    }
}

async function handleCreateOrder(e) {
    e.preventDefault();

    const items = [];
    document.querySelectorAll('.order-item-row').forEach(row => {
        items.push({
            title: row.querySelector('.oi-title').value,
            quantity: row.querySelector('.oi-qty').value,
            unit_price: row.querySelector('.oi-price').value
        });
    });

    const payload = {
        client_id: parseInt(document.getElementById('order-client').value),
        title: document.getElementById('order-title').value,
        price: document.getElementById('order-price').value,
        comment: document.getElementById('order-comment').value || null,
        status: 'new',
        items: items
    };

    try {
        await apiPost('/orders', payload);
        closeModal();
        showToast('Заказ успешно создан', 'success');
        loadOrders();
    } catch (err) {
        showToast(err.message || 'Ошибка создания', 'error');
    }
}

async function deleteOrder(id) {
    if (!confirm('Вы уверены, что хотите удалить заказ?')) return;
    try {
        await apiDelete(`/orders/${id}`);
        showToast('Заказ удален', 'success');
        loadOrders();
    } catch (e) {
        showToast('Ошибка удаления', 'error');
    }
}


// --- Tasks Module ---
let cachedOrders = [];

async function loadTasks() {
    el.pageTitle.textContent = 'Задачи';
    el.pageSubtitle.textContent = 'Задачи по заказам и проектам';

    // Page Actions with Toggle
    el.pageActions.innerHTML = `
        <div style="display: flex; gap: 1rem; align-items: center;">
            <div class="view-toggle-btn">
                <button class="${state.taskViewMode === 'table' ? 'active' : ''}" onclick="switchTaskView('table')">Список</button>
                <button class="${state.taskViewMode === 'kanban' ? 'active' : ''}" onclick="switchTaskView('kanban')">Доска</button>
            </div>
            <button class="btn btn-primary" onclick="openCreateTaskModal()">+ Новая задача</button>
        </div>
    `;

    try {
        const [tasks, orders] = await Promise.all([
            apiGet('/tasks'),
            apiGet('/orders').catch(() => [])
        ]);
        cachedOrders = orders;

        if (state.taskViewMode === 'kanban') {
            renderTaskKanban(tasks);
        } else {
            renderTasksTable(tasks);
        }
    } catch (e) {
        showToast('Ошибка загрузки задач', 'error');
    }
}

function switchTaskView(mode) {
    state.taskViewMode = mode;
    loadTasks();
}

function renderTaskKanban(tasks) {
    el.tableContainer.style.display = 'none';
    el.viewKanban.style.display = 'block';

    const columns = [
        { id: 'new', title: 'Новое', icon: '✨' },
        { id: 'in_progress', title: 'В работе', icon: '⚡' },
        { id: 'done', title: 'Готово', icon: '🎉' }
    ];

    el.kanbanContainer.innerHTML = columns.map(col => {
        const colTasks = tasks.filter(t => t.status === col.id);
        return `
            <div class="kanban-column" data-status="${col.id}">
                <div class="kanban-column-header">
                    <h4>${col.icon} ${col.title}</h4>
                    <span class="kanban-column-count">${colTasks.length}</span>
                </div>
                <div class="kanban-column-content" id="kanban-col-${col.id}">
                    ${colTasks.length === 0 ? `
                        <div class="text-muted text-sm text-center" style="padding: 3rem 1rem; opacity: 0.5;">
                            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🏜️</div>
                            Здесь пока пусто
                        </div>
                    ` : ''}
                    ${colTasks.map(t => {
            const next = nextTaskStatus(t.status);
            const dueDate = t.due_date ? new Date(t.due_date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }) : 'Без срока';
            return `
                            <div class="kanban-card">
                                <span class="kanban-card-title">${escapeHtml(t.title)}</span>
                                ${t.order_title ? `<a href="#" class="kanban-card-order" onclick="viewOrder(${t.order_id}); return false;">📦 ${escapeHtml(t.order_title)}</a>` : ''}
                                <div class="kanban-card-meta">
                                    <div class="kanban-card-date">
                                        <span>📅</span>
                                        <span>${dueDate}</span>
                                    </div>
                                    <span class="kanban-card-id">#${t.id}</span>
                                </div>
                                <div class="kanban-card-actions">
                                    ${next ? `<button class="btn btn-xs btn-primary" onclick="advanceTask(${t.id}, '${next}')">👉 ${translateTaskStatus(next)}</button>` : ''}
                                    <button class="btn btn-xs btn-outline" style="color:var(--danger);" onclick="deleteTask(${t.id})">🗑️</button>
                                </div>
                            </div>
                        `;
        }).join('')}
                </div>
            </div>
        `;
    }).join('');
}

function translateTaskStatus(s) {
    return { 'new': 'Новая', 'in_progress': 'В работе', 'done': 'Готово' }[s] || s;
}

function taskStatusBadge(s) {
    const cls = { 'new': 'badge-info', 'in_progress': 'badge-warning', 'done': 'badge-success' }[s] || '';
    return `<span class="badge ${cls}">${translateTaskStatus(s)}</span>`;
}

function nextTaskStatus(s) {
    return { 'new': 'in_progress', 'in_progress': 'done' }[s] || null;
}

function renderTasksTable(tasks) {
    el.tableContainer.style.display = 'block';
    el.viewKanban.style.display = 'none';
    el.tableHead.innerHTML = `<tr><th>ЗАДАЧА</th><th>ЗАКАЗ</th><th>СТАТУС</th><th>ДЕДЛАЙН</th><th>ДЕЙСТВИЯ</th></tr>`;

    if (!tasks.length) {
        el.tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem; color:var(--text-muted);">Нет задач. Создайте первую!</td></tr>';
        el.emptyState.style.display = 'none';
        return;
    }
    el.emptyState.style.display = 'none';

    el.tableBody.innerHTML = tasks.map(t => {
        const next = nextTaskStatus(t.status);
        const advanceBtn = next ? `<button class="btn btn-sm btn-outline" onclick="advanceTask(${t.id}, '${next}')">${translateTaskStatus(next)}</button>` : '';
        return `
        <tr style="${t.status === 'done' ? 'opacity:0.5;' : ''}">
            <td class="fw-600 ${t.status === 'done' ? 'text-muted' : ''}" style="${t.status === 'done' ? 'text-decoration:line-through' : ''}">${escapeHtml(t.title)}</td>
            <td>${t.order_title ? `<a href="#" onclick="viewOrder(${t.order_id}); return false;" style="color:var(--primary);">${escapeHtml(t.order_title)}</a>` : '<span class="text-muted">—</span>'}</td>
            <td>${taskStatusBadge(t.status)}</td>
            <td>${t.due_date ? new Date(t.due_date).toLocaleDateString('ru-RU') : '<span class="text-muted">—</span>'}</td>
            <td>
                ${advanceBtn}
                <button class="btn btn-sm btn-outline" style="color:var(--danger); border-color:var(--danger);" onclick="deleteTask(${t.id})">Удалить</button>
            </td>
        </tr>`;
    }).join('');
}

function openCreateTaskModal(preselectedOrderId) {
    const orderOptions = cachedOrders.map(o => `<option value="${o.id}" ${o.id === preselectedOrderId ? 'selected' : ''}>${escapeHtml(o.title)}</option>`).join('');

    showModal(`
        <div class="modal-header">
            <h3>Новая задача</h3>
            <button class="btn-close" onclick="closeModal()">×</button>
        </div>
        <form id="form-create-task" onsubmit="handleCreateTask(event)">
            <div class="input-group">
                <label>Название задачи</label>
                <input type="text" id="task-title" required maxlength="300">
            </div>
            <div class="input-group">
                <label>Описание</label>
                <textarea id="task-description" rows="2" maxlength="2000"></textarea>
            </div>
            <div class="input-group">
                <label>Привязка к заказу</label>
                <select id="task-order">
                    <option value="">— Без привязки —</option>
                    ${orderOptions}
                </select>
            </div>
            <div class="input-group">
                <label>Дедлайн</label>
                <input type="date" id="task-due">
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;">
                <button type="button" class="btn btn-outline" onclick="closeModal()">Отмена</button>
                <button type="submit" class="btn btn-primary">Создать</button>
            </div>
        </form>
    `);
}

async function handleCreateTask(e) {
    e.preventDefault();
    const due = document.getElementById('task-due').value;
    const orderId = document.getElementById('task-order').value;
    const payload = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value || null,
        order_id: orderId ? parseInt(orderId) : null,
        due_date: due ? new Date(due).toISOString() : null
    };
    try {
        await apiPost('/tasks', payload);
        closeModal();
        showToast('Задача создана', 'success');
        loadTasks();
    } catch (err) {
        showToast(err.message || 'Ошибка создания', 'error');
    }
}

async function advanceTask(id, newStatus) {
    try {
        await apiPut(`/tasks/${id}`, { status: newStatus });
        if (state.currentView === 'reminders') loadTasks();
        showToast('Статус обновлён', 'success');
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

async function deleteTask(id) {
    if (!confirm('Удалить эту задачу?')) return;
    try {
        await apiDelete(`/tasks/${id}`);
        showToast('Задача удалена', 'success');
        loadTasks();
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}

async function loadOrderTasks(orderId) {
    const container = document.getElementById('order-tasks-list');
    if (!container) return;
    try {
        const tasks = await apiGet(`/tasks?order_id=${orderId}`);
        if (!tasks.length) {
            container.innerHTML = '<span class="text-muted">Нет задач</span>';
            return;
        }
        container.innerHTML = tasks.map(t => {
            const next = nextTaskStatus(t.status);
            const advBtn = next ? `<button class="btn btn-sm btn-outline" onclick="advanceTask(${t.id}, '${next}'); setTimeout(() => loadOrderTasks(${orderId}), 300);" style="padding:0.1rem 0.4rem; font-size:0.75rem;">${translateTaskStatus(next)}</button>` : '';
            return `<div style="display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid var(--border);">
                <span class="${t.status === 'done' ? 'text-muted' : ''}" style="${t.status === 'done' ? 'text-decoration:line-through;' : ''}">${escapeHtml(t.title)}</span>
                <span style="display:flex; gap:0.3rem; align-items:center;">${taskStatusBadge(t.status)} ${advBtn}</span>
            </div>`;
        }).join('');
    } catch (e) {
        container.innerHTML = '<span class="text-muted">Ошибка загрузки</span>';
    }
}

// --- Activity Module ---
async function loadActivity() {
    el.pageTitle.textContent = "Журнал";
    el.pageSubtitle.textContent = "Последние действия в системе";
    el.pageActions.innerHTML = ``;
    try {
        const logs = await apiGet('/activity');
        renderActivityTable(logs);
    } catch (e) { showToast('Ошибка загрузки логов', 'error'); }
}

function renderActivityTable(logs) {
    el.tableHead.innerHTML = `
        <tr><th>Время</th><th>Кто</th><th>Действие</th><th>Объект</th></tr>
            `;
    if (logs.length === 0) {
        el.tableBody.innerHTML = '';
        el.emptyState.style.display = 'block';
    } else {
        el.emptyState.style.display = 'none';
        el.tableBody.innerHTML = logs.map(l => `
            <tr>
                <td class="text-muted text-sm">${new Date(l.created_at).toLocaleString()}</td>
                <td>User#${l.user_id || '?'}</td>
                <td><span class="badge in_progress">${l.action}</span></td>
                <td class="fw-600">${escapeHtml(l.entity_type)} #${l.entity_id || ''} <span class="text-muted fw-400"> ${escapeHtml(l.message || '')}</span></td>
            </tr>
        `).join('');
    }
}

// --- Settings Module ---
async function loadSettings() {
    el.pageTitle.textContent = "Настройки системы";
    el.pageSubtitle.textContent = "Управление, импорт и экспорт данных";
    el.pageActions.innerHTML = ``;

    el.tableHead.innerHTML = `<tr><th>Функция</th><th>Описание</th><th>Действие</th></tr> `;
    el.emptyState.style.display = 'none';

    el.tableBody.innerHTML = `
        <tr>
            <td class="fw-600">Пользователи</td>
            <td class="text-muted">Просмотр сотрудников и генерация инвайт-ссылок</td>
            <td><button class="btn btn-sm btn-outline" onclick="openUsersModal()">Управление</button></td>
        </tr>
        <tr>
            <td class="fw-600">Экспорт клиентов</td>
            <td class="text-muted">Скачивание базы клиентов в формате CSV</td>
            <td><a href="/api/v1/export/clients.csv" class="btn btn-sm btn-outline" target="_blank">Скачать</a></td>
        </tr>
        <tr>
            <td class="fw-600">Экспорт заказов</td>
            <td class="text-muted">Скачивание базы заказов с балансами в CSV</td>
            <td><a href="/api/v1/export/orders.csv" class="btn btn-sm btn-outline" target="_blank">Скачать</a></td>
        </tr>
        <tr>
            <td class="fw-600">Импорт клиентов</td>
            <td class="text-muted">Загрузка базы клиентов из CSV файла</td>
            <td><button class="btn btn-sm btn-outline" onclick="openImportModal('clients')">Загрузить CSV</button></td>
        </tr>
        <tr>
            <td class="fw-600">Импорт заказов</td>
            <td class="text-muted">Загрузка базы заказов из CSV файла</td>
            <td><button class="btn btn-sm btn-outline" onclick="openImportModal('orders')">Загрузить CSV</button></td>
        </tr>
    `;
}

async function openUsersModal() {
    showModal(`
        <div class="modal-header">
            <h3>Пользователи системы</h3>
            <button class="btn-close" onclick="closeModal()">×</button>
        </div>
        <div id="users-modal-content" class="p-4 text-center">
            <p>Загрузка...</p>
        </div>
    `);

    try {
        const [users, invites] = await Promise.all([
            apiGet('/users'),
            apiGet('/invites/invites').catch(() => [])
        ]);

        let html = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h4 style="margin:0;">Активные пользователи</h4>
            </div>
            <table class="data-table" style="margin-bottom: 30px;">
                <thead><tr><th>Email</th><th>Роль</th><th>Создан</th></tr></thead>
                <tbody>
                    ${users.map(u => `<tr>
                        <td class="fw-600">${escapeHtml(u.email)}</td>
                        <td><span class="badge in_progress">${u.role}</span></td>
                        <td class="text-muted">${new Date(u.created_at).toLocaleDateString()}</td>
                    </tr>`).join('')}
                </tbody>
            </table>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h4 style="margin:0;">Приглашения</h4>
                <button class="btn btn-sm btn-primary" onclick="createInvite()">Сгенерировать ссылку</button>
            </div>
            <table class="data-table">
                <thead><tr><th>Email</th><th>Роль</th><th>Статус</th><th>Ссылка</th></tr></thead>
                <tbody>
                    ${invites.length === 0 ? `<tr><td colspan="4" class="text-center text-muted">Нет активных приглашений</td></tr>` :
                invites.map(i => `<tr>
                        <td>${escapeHtml(i.email)}</td>
                        <td><span class="badge in_progress">${i.role}</span></td>
                        <td><span class="badge ${i.accepted_at ? 'success' : 'new'}">${i.accepted_at ? 'Принято' : 'Ожидает'}</span></td>
                        <td>${!i.accepted_at ? `<input type="text" readonly value="${window.location.origin}/?invite=${i.token}" style="padding:4px; font-size:12px; width:150px; border:1px solid var(--border);" onclick="this.select()">` : '-'}</td>
                    </tr>`).join('')}
                </tbody>
            </table>
    `;
        document.getElementById('users-modal-content').innerHTML = html;
        document.getElementById('users-modal-content').className = ''; // remove centering
    } catch (e) {
        document.getElementById('users-modal-content').innerHTML = `
        <p class="text-danger" style="margin-top: 20px;">У вас нет прав администратора для просмотра пользователей.</p>
            `;
    }
}

async function createInvite() {
    const email = prompt("Введите Email для приглашения:");
    if (!email) return;
    try {
        await apiPost('/invites/invites', { email, role: 'manager' });
        showToast('Приглашение создано', 'success');
        openUsersModal(); // reload modal
    } catch (e) {
        showToast('Ошибка создания', 'error');
    }
}

function openImportModal(type) {
    const typeLabel = type === 'clients' ? 'клиентов' : 'заказов';
    showModal(`
            <div class="modal-header">
            <h3>Загрузка ${typeLabel} (CSV)</h3>
            <button class="btn-close" onclick="closeModal()">×</button>
        </div>
        <form id="form-import" onsubmit="handleImport(event, '${type}')" style="padding: 10px 0;">
            <div class="input-group">
                <label>Выберите CSV файл</label>
                <input type="file" id="import-file" accept=".csv" required style="padding: 10px; border: 1px dashed var(--border); width: 100%; border-radius: 6px;">
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;">
                <button type="button" class="btn btn-outline" onclick="closeModal()">Отмена</button>
                <button type="submit" class="btn btn-primary" id="btn-import">Загрузить</button>
            </div>
        </form>
    `);
}

async function handleImport(e, type) {
    e.preventDefault();
    const fileInput = document.getElementById('import-file');
    if (!fileInput.files.length) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('skip_errors', 'true');
    formData.append('dry_run', 'false');

    const btn = document.getElementById('btn-import');
    btn.textContent = 'Загрузка...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE} /imports/${type}/csv`, {
            method: 'POST',
            body: formData,
            headers: { 'Authorization': `Bearer ${state.token}` }
        });

        if (!res.ok) throw new Error('File upload failed');
        const data = await res.json();

        showToast(`Успешно импортировано: ${data.imported_rows}. Ошибок: ${data.failed_rows}`, 'success');
        closeModal();
    } catch (err) {
        showToast('Ошибка импорта', 'error');
        btn.textContent = 'Загрузить';
        btn.disabled = false;
    }
}

// --- Order Details / Payments Module ---
async function viewOrder(id) {
    showModal(`
        <div class="modal-header">
            <h3>Заказ #${id}</h3>
            <button class="btn-close" onclick="closeModal()">×</button>
        </div>
        <div id="order-details-content" class="p-4 text-center">
            <p>Загрузка...</p>
        </div>
    `);

    try {
        const summary = await apiGet(`/orders/${id}/summary`);
        const { order, client, balance, payments } = summary;

        let html = `
            <div style="background: var(--bg-surface); padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid var(--border);">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div><span class="text-muted text-sm">Название</span><br><span class="fw-600">${escapeHtml(order.title)}</span></div>
                    <div><span class="text-muted text-sm">Клиент</span><br><span>${escapeHtml(client.name)}</span></div>
                    <div><span class="text-muted text-sm">Стоимость</span><br><span style="font-size: 1.1rem; font-weight: bold;">${formatMoney(order.price)} ₽</span></div>
                    <div><span class="text-muted text-sm">Баланс (Долг)</span><br><span style="color: ${balance > 0 ? 'var(--danger)' : 'var(--success)'}; font-weight: bold;">${formatMoney(balance)} ₽</span></div>
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin:0;">Состав заказа</h4>
            </div>
            
            <table class="data-table" style="margin-bottom: 20px;">
                <thead><tr><th>Название</th><th>Кол-во</th><th>Цена шт.</th><th>Сумма</th></tr></thead>
                <tbody>
                    ${(!order.items || order.items.length === 0) ? `<tr><td colspan="4" class="text-center text-muted">Нет позиций</td></tr>` : ''}
                    ${(order.items || []).map(i => `<tr>
                        <td class="fw-600">${escapeHtml(i.title)}</td>
                        <td>${i.quantity}</td>
                        <td>${formatMoney(i.unit_price)} ₽</td>
                        <td class="fw-600">${formatMoney(i.total_price)} ₽</td>
                    </tr>`).join('')}
                </tbody>
            </table>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin:0;">Платежи</h4>
            </div>
            
            <table class="data-table" style="margin-bottom: 20px;">
                <thead><tr><th>ID</th><th>Сумма</th><th>Дата</th><th></th></tr></thead>
                <tbody>
                    ${payments.length === 0 ? `<tr><td colspan="4" class="text-center text-muted">Нет платежей</td></tr>` : ''}
                    ${payments.map(p => `<tr>
                        <td class="text-muted">#${p.id}</td>
                        <td class="fw-600 text-success">+${formatMoney(p.amount)} ₽</td>
                        <td>${new Date(p.payment_date).toLocaleDateString()}</td>
                        <td class="actions"><button class="btn btn-sm btn-outline btn-danger" onclick="deletePayment(${p.id}, ${order.id})">Удалить</button></td>
                    </tr>`).join('')}
                </tbody>
            </table>

            <form onsubmit="handleAddPayment(event, ${order.id})" style="display: flex; gap: 10px; background: var(--bg-surface); padding: 10px; border: 1px solid var(--border); border-radius: 8px; align-items: flex-end;">
                <div style="flex-grow: 1;">
                    <label style="font-size: 12px; margin-bottom: 4px; display: block;">Добавить платеж</label>
                    <input type="number" id="new-payment-amount" step="0.01" min="0.01" max="${balance > 0 ? balance : ''}" placeholder="Сумма" required style="width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 4px;">
                </div>
                <button type="submit" class="btn btn-primary" ${balance <= 0 ? 'disabled' : ''}>Оплатить</button>
            </form>

            <div style="display: flex; justify-content: space-between; align-items: center; margin: 20px 0 10px;">
                <h4 style="margin:0;">Задачи по заказу</h4>
                <button class="btn btn-outline btn-sm" onclick="openCreateTaskModal(${order.id})" style="padding: 0.2rem 0.6rem; font-size: 0.8rem;">+ Задача</button>
            </div>
            <div id="order-tasks-list" style="font-size: 0.9rem; color: var(--text-muted);">Загрузка...</div>
        `;
        document.getElementById('order-details-content').innerHTML = html;
        document.getElementById('order-details-content').className = '';

        // Load tasks for this order
        loadOrderTasks(order.id);
    } catch (e) {
        document.getElementById('order-details-content').innerHTML = `<p class="text-danger">Ошибка загрузки заказа</p>`;
    }
}

async function handleAddPayment(e, orderId) {
    e.preventDefault();
    const amount = document.getElementById('new-payment-amount').value;
    try {
        await apiPost('/payments', {
            order_id: orderId,
            amount: parseFloat(amount),
            payment_date: new Date().toISOString().split('T')[0]
        });
        showToast('Платеж добавлен', 'success');
        viewOrder(orderId); // reload modal
        if (state.currentView === 'orders') loadOrders();
    } catch (err) {
        showToast('Ошибка при добавлении платежа: ' + err.message, 'error');
    }
}

async function deletePayment(paymentId, orderId) {
    if (!confirm('Удалить этот платеж?')) return;
    try {
        await apiDelete(`/payments/${paymentId}`);
        showToast('Платеж удален', 'success');
        viewOrder(orderId); // reload modal
        if (state.currentView === 'orders') loadOrders();
    } catch (e) {
        showToast('Ошибка', 'error');
    }
}


// --- API Client ---
async function apiFetch(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(state.token ? { 'Authorization': `Bearer ${state.token}` } : {})
    };

    const res = await fetch(API_BASE + url, { ...options, headers });

    if (res.status === 401 && url !== '/auth/login' && url !== '/auth/logout') {
        handleLogout();
        throw new Error('Unauthorized');
    }

    if (!res.ok) {
        let err;
        try {
            const data = await res.json();
            err = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        } catch (e) { err = res.statusText; }
        throw new Error(err || 'Server Error');
    }

    if (res.status === 204) return null;
    return await res.json();
}

const apiGet = (url) => apiFetch(url, { method: 'GET' });
const apiPost = (url, body) => apiFetch(url, { method: 'POST', body: JSON.stringify(body) });
const apiPut = (url, body) => apiFetch(url, { method: 'PUT', body: JSON.stringify(body) });
const apiDelete = (url) => apiFetch(url, { method: 'DELETE' });


// --- Utilities ---
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ?
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" class="text-success"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>' :
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" class="text-danger"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>';

    toast.innerHTML = `
        ${icon}
        <span style="font-size: 0.875rem; font-weight: 500;">${escapeHtml(message)}</span>
    `;

    el.toastContainer.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function showModal(html) {
    el.dynamicModal.innerHTML = html;
    el.modalContainer.classList.add('active');
}

function closeModal() {
    el.modalContainer.classList.remove('active');
    setTimeout(() => el.dynamicModal.innerHTML = '', 200);
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function translateStatus(status) {
    const map = {
        'new': 'Новый',
        'in_progress': 'В работе',
        'done': 'Выполнен',
        'canceled': 'Отменён',
        'pending': 'Ожидает'
    };
    return map[status] || status;
}

function formatMoney(num) {
    return Number(num).toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// --- Catalog Module ---
async function loadCatalog() {
    el.pageTitle.textContent = 'Каталог';
    el.pageSubtitle.textContent = 'Товары и услуги для быстрого добавления в заказы';
    el.pageActions.innerHTML = `<button class="btn btn-primary" onclick="openCreateProductModal()">+ Добавить товар</button>`;

    try {
        const products = await apiGet('/products?include_inactive=true');
        cachedProducts = products;
        renderCatalogTable(products);
    } catch (err) {
        showToast('Ошибка загрузки каталога', 'error');
    }
}

function renderCatalogTable(products) {
    el.tableHead.innerHTML = `<tr><th>НАИМЕНОВАНИЕ</th><th>ОПИСАНИЕ</th><th>ЦЕНА</th><th>СТАТУС</th><th>ДЕЙСТВИЯ</th></tr>`;

    if (!products.length) {
        el.tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem; color:var(--text-muted);">Каталог пуст. Добавьте первый товар или услугу.</td></tr>';
        return;
    }

    el.tableBody.innerHTML = products.map(p => `
        <tr>
            <td class="fw-600">${escapeHtml(p.name)}</td>
            <td class="text-muted">${escapeHtml(p.description || '—')}</td>
            <td>${formatMoney(p.price)} ₽</td>
            <td><span class="badge ${p.is_active ? 'badge-success' : 'badge-muted'}">${p.is_active ? 'Активен' : 'Архив'}</span></td>
            <td>
                <button class="btn btn-outline btn-sm" onclick="openEditProductModal(${p.id})">Ред.</button>
                <button class="btn btn-outline btn-sm" style="color:var(--danger); border-color:var(--danger);" onclick="deleteProduct(${p.id})">Удалить</button>
            </td>
        </tr>
    `).join('');
}

function openCreateProductModal() {
    showModal(`
        <div class="modal-header">
            <h3>Новый товар / услуга</h3>
            <button class="btn-close" onclick="closeModal()">×</button>
        </div>
        <form id="form-create-product" onsubmit="handleCreateProduct(event)">
            <div class="input-group">
                <label>Наименование</label>
                <input type="text" id="product-name" required maxlength="200">
            </div>
            <div class="input-group">
                <label>Описание</label>
                <textarea id="product-description" rows="2" maxlength="1000"></textarea>
            </div>
            <div class="input-group">
                <label>Базовая цена (₽)</label>
                <input type="number" id="product-price" step="0.01" min="0" value="0.00" required>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;">
                <button type="button" class="btn btn-outline" onclick="closeModal()">Отмена</button>
                <button type="submit" class="btn btn-primary">Создать</button>
            </div>
        </form>
    `);
}

async function handleCreateProduct(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('product-name').value,
        description: document.getElementById('product-description').value || null,
        price: document.getElementById('product-price').value
    };
    try {
        await apiPost('/products', payload);
        closeModal();
        showToast('Товар добавлен в каталог', 'success');
        loadCatalog();
    } catch (err) {
        showToast(err.message || 'Ошибка создания', 'error');
    }
}

function openEditProductModal(id) {
    const product = cachedProducts.find(p => p.id === id);
    if (!product) return;

    showModal(`
        <div class="modal-header">
            <h3>Редактировать товар</h3>
            <button class="btn-close" onclick="closeModal()">×</button>
        </div>
        <form id="form-edit-product" onsubmit="handleEditProduct(event, ${id})">
            <div class="input-group">
                <label>Наименование</label>
                <input type="text" id="product-name" value="${escapeHtml(product.name)}" required maxlength="200">
            </div>
            <div class="input-group">
                <label>Описание</label>
                <textarea id="product-description" rows="2" maxlength="1000">${escapeHtml(product.description || '')}</textarea>
            </div>
            <div class="input-group">
                <label>Базовая цена (₽)</label>
                <input type="number" id="product-price" step="0.01" min="0" value="${product.price}" required>
            </div>
            <div class="input-group">
                <label>Статус</label>
                <select id="product-active">
                    <option value="true" ${product.is_active ? 'selected' : ''}>Активен</option>
                    <option value="false" ${!product.is_active ? 'selected' : ''}>Архив</option>
                </select>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1.5rem;">
                <button type="button" class="btn btn-outline" onclick="closeModal()">Отмена</button>
                <button type="submit" class="btn btn-primary">Сохранить</button>
            </div>
        </form>
    `);
}

async function handleEditProduct(e, id) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('product-name').value,
        description: document.getElementById('product-description').value || null,
        price: document.getElementById('product-price').value,
        is_active: document.getElementById('product-active').value === 'true'
    };
    try {
        await apiPut(`/products/${id}`, payload);
        closeModal();
        showToast('Товар обновлён', 'success');
        loadCatalog();
    } catch (err) {
        showToast(err.message || 'Ошибка обновления', 'error');
    }
}

async function deleteProduct(id) {
    if (!confirm('Удалить этот товар из каталога?')) return;
    try {
        await apiDelete(`/products/${id}`);
        showToast('Товар удалён', 'success');
        loadCatalog();
    } catch (err) {
        showToast(err.message || 'Ошибка удаления', 'error');
    }
}

// Start sequence
init();
