package repository

import (
	"deskly-crm-go/internal/domain"
	"gorm.io/gorm"
)

type ClientRepository interface {
	Create(client *domain.Client) error
	GetByID(id uint, tenantID uint) (*domain.Client, error)
	List(tenantID uint) ([]domain.Client, error)
	Update(client *domain.Client) error
	Delete(id uint, tenantID uint) error
}

type clientRepo struct {
	db *gorm.DB
}

func NewClientRepo(db *gorm.DB) ClientRepository {
	return &clientRepo{db: db}
}

func (r *clientRepo) Create(c *domain.Client) error { return r.db.Create(c).Error }
func (r *clientRepo) GetByID(id, tID uint) (*domain.Client, error) {
	var c domain.Client
	err := r.db.Where("id = ? AND tenant_id = ?", id, tID).First(&c).Error
	return &c, err
}
func (r *clientRepo) List(tID uint) ([]domain.Client, error) {
	var list []domain.Client
	err := r.db.Where("tenant_id = ?", tID).Find(&list).Error
	return list, err
}
func (r *clientRepo) Update(c *domain.Client) error { return r.db.Save(c).Error }
func (r *clientRepo) Delete(id, tID uint) error {
	return r.db.Where("id = ? AND tenant_id = ?", id, tID).Delete(&domain.Client{}).Error
}
