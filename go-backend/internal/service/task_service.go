package service

import (
	"errors"
	"time"

	"deskly-crm-go/internal/domain"
	"deskly-crm-go/internal/repository"
)

type TaskService interface {
	ListTasks(tenantID uint, status string, orderID string) ([]domain.Task, error)
	CreateTask(tenantID uint, title, description string, orderID uint, clientID uint, dueDate *string) (*domain.Task, error)
	UpdateTask(id, tenantID uint, title, description, status string, clientID uint, dueDate *string) error
	DeleteTask(id, tenantID uint) error
}

type taskService struct {
	repo repository.TaskRepository
}

func NewTaskService(repo repository.TaskRepository) TaskService {
	return &taskService{repo: repo}
}

func (s *taskService) ListTasks(tenantID uint, status, orderID string) ([]domain.Task, error) {
	return s.repo.List(tenantID, status, orderID)
}

func (s *taskService) CreateTask(tenantID uint, title, description string, orderID uint, clientID uint, dueDate *string) (*domain.Task, error) {
	if title == "" {
		return nil, errors.New("название обязательно")
	}
	task := &domain.Task{
		BaseEntity:  domain.BaseEntity{TenantID: tenantID},
		Title:       title,
		Description: description,
		Status:      "new",
		OrderID:     orderID,
		ClientID:    clientID,
	}
	if dueDate != nil && *dueDate != "" {
		t, err := time.Parse("2006-01-02", *dueDate)
		if err == nil {
			task.DueDate = &t
		}
	}
	return task, s.repo.Create(task)
}

func (s *taskService) UpdateTask(id, tenantID uint, title, description, status string, clientID uint, dueDate *string) error {
	task, err := s.repo.GetByID(id, tenantID)
	if err != nil {
		return errors.New("задача не найдена")
	}
	if title != "" {
		task.Title = title
	}
	task.Description = description
	if status != "" {
		task.Status = status
	}
	task.ClientID = clientID
	if dueDate != nil {
		if *dueDate == "" {
			task.DueDate = nil
		} else {
			t, err := time.Parse("2006-01-02", *dueDate)
			if err == nil {
				task.DueDate = &t
			}
		}
	}
	return s.repo.Update(task)
}

func (s *taskService) DeleteTask(id, tenantID uint) error {
	return s.repo.Delete(id, tenantID)
}
