package repository

import (
	"deskly-crm-go/internal/domain"
	"gorm.io/gorm"
)

type ProductRepository interface {
	Create(p *domain.Product) error
	GetByID(id uint, tID uint) (*domain.Product, error)
	List(tID uint) ([]domain.Product, error)
}

type productRepo struct {
	db *gorm.DB
}

func NewProductRepo(db *gorm.DB) ProductRepository {
	return &productRepo{db: db}
}

func (r *productRepo) Create(p *domain.Product) error { return r.db.Create(p).Error }
func (r *productRepo) GetByID(id, tID uint) (*domain.Product, error) {
	var p domain.Product
	err := r.db.Where("id = ? AND tenant_id = ?", id, tID).First(&p).Error
	return &p, err
}
func (r *productRepo) List(tID uint) ([]domain.Product, error) {
	var list []domain.Product
	err := r.db.Where("tenant_id = ?", tID).Find(&list).Error
	return list, err
}
