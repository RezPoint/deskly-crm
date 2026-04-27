package handler

import (
	"encoding/json"
	"fmt"
	"net/http"

	"deskly-crm-go/internal/domain"
	"github.com/shopspring/decimal"
	"gorm.io/gorm"
)

type PaymentHandler struct {
	db *gorm.DB
}

func NewPaymentHandler(db *gorm.DB) *PaymentHandler {
	return &PaymentHandler{db: db}
}

func (h *PaymentHandler) CreatePayment(w http.ResponseWriter, r *http.Request) {
	var req struct {
		OrderID uint            `json:"order_id"`
		Amount  decimal.Decimal `json:"amount"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	payment := domain.Payment{
		BaseEntity: domain.BaseEntity{TenantID: 1},
		OrderID:    req.OrderID,
		Amount:     req.Amount,
	}

	if err := h.db.Create(&payment).Error; err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	logActivity(h.db, 1, "payment", "order", req.OrderID, fmt.Sprintf("Оплата %s ₽ по заказу #%d", req.Amount.String(), req.OrderID))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(payment)
}
