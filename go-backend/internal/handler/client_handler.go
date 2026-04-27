package handler

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"

	"deskly-crm-go/internal/domain"
	"deskly-crm-go/internal/service"
	"github.com/shopspring/decimal"
	"gorm.io/gorm"
)

type ClientHandler struct {
	svc service.ClientService
	db  *gorm.DB
}

func NewClientHandler(svc service.ClientService, db *gorm.DB) *ClientHandler {
	return &ClientHandler{svc: svc, db: db}
}

func (h *ClientHandler) CreateClient(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name     string `json:"name"`
		Phone    string `json:"phone"`
		Telegram string `json:"telegram"`
		Notes    string `json:"notes"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Ошибка парсинга JSON", http.StatusBadRequest)
		return
	}

	client, err := h.svc.CreateClient(1, req.Name, req.Phone, req.Telegram, req.Notes)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	logActivity(h.db, 1, "create", "client", client.ID, fmt.Sprintf("Клиент создан: %s", client.Name))

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(client)
}

func (h *ClientHandler) ListClients(w http.ResponseWriter, r *http.Request) {
	var clients []domain.Client
	var err error

	if q := r.URL.Query().Get("q"); q != "" {
		clients, err = h.svc.SearchClients(1, q)
	} else {
		clients, err = h.svc.ListClients(1)
	}

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(clients)
}

func (h *ClientHandler) GetClient(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, _ := strconv.ParseUint(idStr, 10, 32)

	client, err := h.svc.GetClient(uint(id), 1)
	if err != nil {
		http.Error(w, "Клиент не найден", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(client)
}

func (h *ClientHandler) GetClientOrders(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, _ := strconv.ParseUint(idStr, 10, 32)

	type clientOrder struct {
		ID         uint            `json:"id"`
		Title      string          `json:"title"`
		Price      decimal.Decimal `json:"price"`
		PaidAmount decimal.Decimal `json:"paid_amount"`
		Status     string          `json:"status"`
		Comment    string          `json:"comment"`
		CreatedAt  interface{}     `json:"created_at"`
	}

	var orders []clientOrder
	h.db.Table("orders").
		Select("orders.id, orders.title, orders.price, COALESCE(SUM(payments.amount), 0) as paid_amount, orders.status, orders.comment, orders.created_at").
		Joins("left join payments on payments.order_id = orders.id").
		Where("orders.client_id = ? AND orders.tenant_id = ? AND orders.deleted_at IS NULL", id, 1).
		Group("orders.id").
		Order("orders.id desc").
		Scan(&orders)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(orders)
}
