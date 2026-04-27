package service

import (
	"deskly-crm-go/internal/domain"
	"deskly-crm-go/internal/repository"
	"github.com/shopspring/decimal"
)

type OrderService interface {
	CreateOrder(tenantID uint, title string, clientID uint, basePrice decimal.Decimal, items []domain.OrderItem) (*domain.Order, error)
	GetOrder(id uint, tenantID uint) (*domain.Order, error)
	ListOrders(tenantID uint, limit, offset int) ([]domain.Order, error)
	DeleteOrder(id uint, tenantID uint) error
	UpdateOrderStatus(id uint, tenantID uint, status string) error
}

type orderService struct {
	repo repository.OrderRepository
}

func NewOrderService(repo repository.OrderRepository) OrderService {
	return &orderService{repo: repo}
}

func (s *orderService) CreateOrder(tenantID uint, title string, clientID uint, basePrice decimal.Decimal, items []domain.OrderItem) (*domain.Order, error) {
	totalSum := basePrice
	
	if len(items) > 0 {
		totalSum = decimal.NewFromInt(0)
		for i := range items {
			items[i].TenantID = tenantID
			items[i].TotalPrice = items[i].Quantity.Mul(items[i].UnitPrice)
			totalSum = totalSum.Add(items[i].TotalPrice)
		}
	}

	order := &domain.Order{
		BaseEntity: domain.BaseEntity{TenantID: tenantID},
		Title:      title,
		ClientID:   clientID,
		Price:      totalSum,
		Status:     "new",
		Items:      items,
	}

	if err := s.repo.Create(order); err != nil {
		return nil, err
	}

	return order, nil
}

func (s *orderService) UpdateOrderStatus(id uint, tenantID uint, status string) error {
	return s.repo.UpdateStatus(id, tenantID, status)
}

func (s *orderService) GetOrder(id uint, tenantID uint) (*domain.Order, error) {
	return s.repo.GetByID(id, tenantID)
}

func (s *orderService) ListOrders(tenantID uint, limit, offset int) ([]domain.Order, error) {
	return s.repo.List(tenantID, limit, offset)
}

func (s *orderService) DeleteOrder(id uint, tenantID uint) error {
	return s.repo.Delete(id, tenantID)
}
