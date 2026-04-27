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

func (h *DashboardHandler) GetRevenue(w http.ResponseWriter, r *http.Request) {
	type Point struct {
		Date   string  `json:"date"`
		Amount float64 `json:"amount"`
	}
	var points []Point
	h.db.Table("payments").
		Select("strftime('%Y-%m-%d', payments.created_at) as date, COALESCE(SUM(payments.amount), 0) as amount").
		Joins("JOIN orders ON orders.id = payments.order_id").
		Where("payments.tenant_id = ? AND payments.created_at >= date('now', '-30 days') AND orders.deleted_at IS NULL", 1).
		Group("strftime('%Y-%m-%d', payments.created_at)").
		Order("date").
		Scan(&points)
	if points == nil {
		points = []Point{}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(points)
}

func (h *DashboardHandler) GetStats(w http.ResponseWriter, r *http.Request) {
	var clientCount int64
	var orderCount int64
	var totalAmount float64
	var actualRevenue float64
	var activeTasks int64

	h.db.Model(&domain.Client{}).Where("tenant_id = ?", 1).Count(&clientCount)
	h.db.Model(&domain.Order{}).Where("tenant_id = ? AND status != ?", 1, "cancelled").Count(&orderCount)
	h.db.Model(&domain.Order{}).Where("tenant_id = ? AND status != ?", 1, "cancelled").Select("COALESCE(SUM(price), 0)").Scan(&totalAmount)
	h.db.Table("payments").
		Joins("join orders on orders.id = payments.order_id").
		Where("orders.deleted_at IS NULL AND payments.tenant_id = ?", 1).
		Select("COALESCE(SUM(payments.amount), 0)").
		Scan(&actualRevenue)
	h.db.Model(&domain.Task{}).Where("tenant_id = ? AND status != ?", 1, "done").Count(&activeTasks)

	// Долг = сумма незакрытых заказов минус оплаченное
	debt := totalAmount - actualRevenue

	// 5 последних заказов (инициализируем как пустой slice чтобы JSON вернул [] а не null)
	recentOrders := make([]struct {
		ID         uint   `json:"id"`
		Title      string `json:"title"`
		Status     string `json:"status"`
		ClientName string `json:"client_name"`
	}, 0)
	h.db.Table("orders").
		Select("orders.id, orders.title, orders.status, clients.name as client_name").
		Joins("left join clients on clients.id = orders.client_id").
		Where("orders.tenant_id = ? AND orders.deleted_at IS NULL", 1).
		Order("orders.id desc").
		Limit(5).
		Scan(&recentOrders)

	stats := map[string]interface{}{
		"clients":      clientCount,
		"orders":       orderCount,
		"total":        totalAmount,
		"revenue":      actualRevenue,
		"debt":         debt,
		"active_tasks": activeTasks,
		"recent_orders": recentOrders,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}
