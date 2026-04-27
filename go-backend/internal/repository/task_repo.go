package repository

import (
	"deskly-crm-go/internal/domain"
	"gorm.io/gorm"
)

type TaskRepository interface {
	List(tenantID uint, status string, orderID string) ([]domain.Task, error)
	Create(task *domain.Task) error
	GetByID(id uint, tenantID uint) (*domain.Task, error)
	Update(task *domain.Task) error
	Delete(id uint, tenantID uint) error
}

type taskRepo struct {
	db *gorm.DB
}

func NewTaskRepo(db *gorm.DB) TaskRepository {
	return &taskRepo{db: db}
}

func (r *taskRepo) List(tenantID uint, status string, orderID string) ([]domain.Task, error) {
	var tasks []domain.Task
	q := r.db.Where("tenant_id = ?", tenantID)
	if status != "" {
		q = q.Where("status = ?", status)
	}
	if orderID != "" {
		q = q.Where("order_id = ?", orderID)
	}
	err := q.Order("CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date").Find(&tasks).Error
	return tasks, err
}

func (r *taskRepo) Create(task *domain.Task) error {
	return r.db.Create(task).Error
}

func (r *taskRepo) GetByID(id uint, tenantID uint) (*domain.Task, error) {
	var task domain.Task
	err := r.db.Where("id = ? AND tenant_id = ?", id, tenantID).First(&task).Error
	return &task, err
}

func (r *taskRepo) Update(task *domain.Task) error {
	return r.db.Save(task).Error
}

func (r *taskRepo) Delete(id uint, tenantID uint) error {
	return r.db.Where("id = ? AND tenant_id = ?", id, tenantID).Delete(&domain.Task{}).Error
}
