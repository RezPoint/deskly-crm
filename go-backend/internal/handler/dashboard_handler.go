package handler

import (
	"encoding/json"
	"net/http"

	"deskly-crm-go/internal/domain"
	"gorm.io/gorm"
)

type DashboardHandler struct {
	db *gorm.DB
}

func NewDashboardHandler(db *gorm.DB) *DashboardHandler {
	return &DashboardHandler{db: db}
}

func (h *DashboardHandler) GetStats(w http.ResponseWriter, r *http.Request) {
	var clientCount int64
	var orderCount int64
	var totalAmount float64
	var actualRevenue float64

	// Считаем клиентов
	h.db.Model(&domain.Client{}).Where("tenant_id = ?", 1).Count(&clientCount)
	
	// Считаем активные заказы
	h.db.Model(&domain.Order{}).Where("tenant_id = ? AND status != ?", 1, "cancelled").Count(&orderCount)

	// Считаем Оборот (сумма всех активных заказов)
	h.db.Model(&domain.Order{}).Where("tenant_id = ? AND status != ?", 1, "cancelled").Select("COALESCE(SUM(price), 0)").Scan(&totalAmount)

	// Считаем Реальную Выручку (сумма всех платежей, привязанных к ЖИВЫМ заказам)
	h.db.Table("payments").
		Joins("join orders on orders.id = payments.order_id").
		Where("orders.deleted_at IS NULL AND payments.tenant_id = ?", 1).
		Select("COALESCE(SUM(payments.amount), 0)").
		Scan(&actualRevenue)

	stats := map[string]interface{}{
		"clients": clientCount,
		"orders":  orderCount,
		"total":   totalAmount,
		"revenue": actualRevenue,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}
