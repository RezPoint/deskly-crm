package service

import (
	"deskly-crm-go/internal/domain"
	"deskly-crm-go/internal/repository"
	"github.com/shopspring/decimal"
)

type ProductService interface {
	CreateProduct(tID uint, name, desc string, price decimal.Decimal) (*domain.Product, error)
	ListProducts(tID uint) ([]domain.Product, error)
}

type productService struct {
	repo repository.ProductRepository
}

func NewProductService(repo repository.ProductRepository) ProductService {
	return &productService{repo: repo}
}

func (s *productService) CreateProduct(tID uint, name, desc string, price decimal.Decimal) (*domain.Product, error) {
	p := &domain.Product{
		BaseEntity:  domain.BaseEntity{TenantID: tID},
		Name:        name,
		Description: desc,
		Price:       price,
		IsActive:    true,
	}
	return p, s.repo.Create(p)
}

func (s *productService) ListProducts(tID uint) ([]domain.Product, error) { return s.repo.List(tID) }
