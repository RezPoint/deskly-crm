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
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "неверный формат JSON", http.StatusBadRequest)
		return
	}
	order, err := h.svc.CreateOrder(1, req.Title, req.ClientID, req.Price, req.Items)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	logActivity(h.db, 1, "create", "order", order.ID, fmt.Sprintf("Заказ создан: %s", order.Title))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(order)
}

func (h *OrderHandler) ListOrders(w http.ResponseWriter, r *http.Request) {
	statusFilter := r.URL.Query().Get("status")
	qFilter := r.URL.Query().Get("q")

	var orders []struct {
		domain.Order
		PaidAmount decimal.Decimal `json:"paid_amount"`
		ClientName string          `json:"client_name"`
	}

	tx := h.db.Table("orders").
		Select("orders.*, COALESCE(SUM(payments.amount), 0) as paid_amount, clients.name as client_name").
		Joins("left join payments on payments.order_id = orders.id").
		Joins("left join clients on clients.id = orders.client_id").
		Where("orders.tenant_id = ? AND orders.deleted_at IS NULL", 1).
		Group("orders.id").
		Order("orders.id desc")

	if statusFilter != "" {
		tx = tx.Where("orders.status = ?", statusFilter)
	}
	if qFilter != "" {
		tx = tx.Where("clients.name LIKE ?", "%"+qFilter+"%")
	}

	tx.Scan(&orders)

	// Подгружаем позиции для каждого заказа
	type orderWithItems struct {
		ID         uint            `json:"id"`
		CreatedAt  interface{}     `json:"created_at"`
		Title      string          `json:"title"`
		ClientID   uint            `json:"client_id"`
		ClientName string          `json:"client_name"`
		Price      decimal.Decimal `json:"price"`
		PaidAmount decimal.Decimal `json:"paid_amount"`
		Status     string          `json:"status"`
		Comment    string          `json:"comment"`
		Items      []domain.OrderItem `json:"items"`
	}

	result := make([]orderWithItems, len(orders))
	for i, o := range orders {
		var items []domain.OrderItem
		h.db.Where("order_id = ?", o.ID).Find(&items)
		result[i] = orderWithItems{
			ID:         o.ID,
			CreatedAt:  o.CreatedAt,
			Title:      o.Title,
			ClientID:   o.ClientID,
			ClientName: o.ClientName,
			Price:      o.Price,
			PaidAmount: o.PaidAmount,
			Status:     o.Status,
			Comment:    o.Comment,
			Items:      items,
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (h *OrderHandler) ListComments(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, _ := strconv.ParseUint(idStr, 10, 32)
	var comments []domain.OrderComment
	h.db.Where("order_id = ? AND tenant_id = ?", id, 1).Order("created_at asc").Find(&comments)
	if comments == nil {
		comments = []domain.OrderComment{}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(comments)
}

func (h *OrderHandler) CreateComment(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, _ := strconv.ParseUint(idStr, 10, 32)
	var req struct {
		Message string `json:"message"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil || req.Message == "" {
		http.Error(w, "сообщение не может быть пустым", http.StatusBadRequest)
		return
	}
	comment := domain.OrderComment{
		BaseEntity: domain.BaseEntity{TenantID: 1},
		OrderID:    uint(id),
		Message:    req.Message,
	}
	h.db.Create(&comment)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(comment)
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
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "неверный формат JSON", http.StatusBadRequest)
		return
	}
	h.svc.UpdateOrderStatus(uint(id), 1, req.Status)
	w.WriteHeader(http.StatusNoContent)
}
