package service

import (
	"deskly-crm-go/internal/domain"
	"deskly-crm-go/internal/repository"
)

type ClientService interface {
	CreateClient(tenantID uint, name, phone, telegram, notes string) (*domain.Client, error)
	GetClient(id, tenantID uint) (*domain.Client, error)
	ListClients(tenantID uint) ([]domain.Client, error)
	SearchClients(tenantID uint, query string) ([]domain.Client, error)
}

type clientService struct {
	repo repository.ClientRepository
}

func NewClientService(repo repository.ClientRepository) ClientService {
	return &clientService{repo: repo}
}

func (s *clientService) CreateClient(tID uint, name, phone, telegram, notes string) (*domain.Client, error) {
	c := &domain.Client{
		BaseEntity: domain.BaseEntity{TenantID: tID},
		Name:       name,
		Phone:      phone,
		Telegram:   telegram,
		Notes:      notes,
	}
	return c, s.repo.Create(c)
}

func (s *clientService) GetClient(id, tID uint) (*domain.Client, error) { return s.repo.GetByID(id, tID) }
func (s *clientService) ListClients(tID uint) ([]domain.Client, error)  { return s.repo.List(tID) }
func (s *clientService) SearchClients(tID uint, query string) ([]domain.Client, error) {
	return s.repo.Search(tID, query)
}
