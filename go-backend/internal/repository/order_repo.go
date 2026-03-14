package repository

import (
	"deskly-crm-go/internal/domain"
	"gorm.io/gorm"
)

type OrderRepository interface {
	Create(order *domain.Order) error
	GetByID(id uint, tenantID uint) (*domain.Order, error)
	List(tenantID uint, limit, offset int) ([]domain.Order, error)
	Delete(id uint, tenantID uint) error
	UpdateStatus(id uint, tenantID uint, status string) error
}

func (r *orderRepo) UpdateStatus(id uint, tenantID uint, status string) error {
	return r.db.Model(&domain.Order{}).Where("id = ? AND tenant_id = ?", id, tenantID).Update("status", status).Error
}

type orderRepo struct {
	db *gorm.DB
}

func NewOrderRepo(db *gorm.DB) OrderRepository {
	return &orderRepo{db: db}
}

func (r *orderRepo) Create(order *domain.Order) error {
	return r.db.Create(order).Error
}

func (r *orderRepo) GetByID(id uint, tenantID uint) (*domain.Order, error) {
	var order domain.Order
	err := r.db.Preload("Items").Where("id = ? AND tenant_id = ?", id, tenantID).First(&order).Error
	return &order, err
}

func (r *orderRepo) List(tenantID uint, limit, offset int) ([]domain.Order, error) {
	var orders []domain.Order
	err := r.db.Where("tenant_id = ?", tenantID).
		Limit(limit).Offset(offset).
		Order("id desc").
		Find(&orders).Error
	return orders, err
}

func (r *orderRepo) Delete(id uint, tenantID uint) error {
	return r.db.Where("id = ? AND tenant_id = ?", id, tenantID).Delete(&domain.Order{}).Error
}
