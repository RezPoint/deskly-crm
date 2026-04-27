package repository

import (
	"deskly-crm-go/internal/domain"
	"gorm.io/gorm"
)

type UserRepository interface {
	Create(user *domain.User) error
	GetByEmail(email string) (*domain.User, error)
	GetByID(id uint) (*domain.User, error)
}

type userRepo struct {
	db *gorm.DB
}

func NewUserRepo(db *gorm.DB) UserRepository {
	return &userRepo{db: db}
}

func (r *userRepo) Create(u *domain.User) error {
	return r.db.Create(u).Error
}

func (r *userRepo) GetByEmail(email string) (*domain.User, error) {
	var user domain.User
	err := r.db.Where("email = ?", email).First(&user).Error
	return &user, err
}

func (r *userRepo) GetByID(id uint) (*domain.User, error) {
	var user domain.User
	err := r.db.First(&user, id).Error
	return &user, err
}
