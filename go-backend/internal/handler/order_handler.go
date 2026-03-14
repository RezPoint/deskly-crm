package handler

import (
	"encoding/json"
	"net/http"
	"strconv"

	"deskly-crm-go/internal/domain"
	"deskly-crm-go/internal/service"
	"github.com/shopspring/decimal"
	"gorm.io/gorm"
)

type OrderHandler struct {
	svc service.OrderService
	db  *gorm.DB
}

func NewOrderHandler(svc service.OrderService, db *gorm.DB) *OrderHandler {
	return &OrderHandler{svc: svc, db: db}
}

func (h *OrderHandler) CreateOrder(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Title    string             `json:"title"`
		ClientID uint               `json:"client_id"`
		Price    decimal.Decimal    `json:"price"`
		Items    []domain.OrderItem `json:"items"`
	}
	json.NewDecoder(r.Body).Decode(&req)
	order, err := h.svc.CreateOrder(1, req.Title, req.ClientID, req.Price, req.Items)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(order)
}

func (h *OrderHandler) ListOrders(w http.ResponseWriter, r *http.Request) {
	var orders []struct {
		domain.Order
		PaidAmount decimal.Decimal `json:"paid_amount"`
	}
	h.db.Table("orders").
		Select("orders.*, COALESCE(SUM(payments.amount), 0) as paid_amount").
		Joins("left join payments on payments.order_id = orders.id").
		Where("orders.tenant_id = ? AND orders.deleted_at IS NULL", 1).
		Group("orders.id").
		Order("orders.id desc").
		Scan(&orders)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(orders)
}

func (h *OrderHandler) GetOrder(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, _ := strconv.ParseUint(idStr, 10, 32)
	order, err := h.svc.GetOrder(uint(id), 1)
	if err != nil {
		http.Error(w, "Заказ не найден", http.StatusNotFound)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(order)
}

func (h *OrderHandler) UpdateStatus(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, _ := strconv.ParseUint(idStr, 10, 32)
	var req struct { Status string `json:"status"` }
	json.NewDecoder(r.Body).Decode(&req)
	h.svc.UpdateOrderStatus(uint(id), 1, req.Status)
	w.WriteHeader(http.StatusNoContent)
}
