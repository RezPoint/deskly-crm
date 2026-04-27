package service

import (
	"errors"
	"time"

	"deskly-crm-go/internal/domain"
	"deskly-crm-go/internal/repository"
	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

type AuthService interface {
	Register(tenantID uint, email, password string) (*domain.User, error)
	Login(email, password string) (string, error)
}

type authService struct {
	repo   repository.UserRepository
	secret string
}

func NewAuthService(repo repository.UserRepository, secret string) AuthService {
	return &authService{repo: repo, secret: secret}
}

func (s *authService) Register(tID uint, email, password string) (*domain.User, error) {
	hash, _ := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	user := &domain.User{
		BaseEntity:   domain.BaseEntity{TenantID: tID},
		Email:        email,
		PasswordHash: string(hash),
	}
	return user, s.repo.Create(user)
}

func (s *authService) Login(email, password string) (string, error) {
	user, err := s.repo.GetByEmail(email)
	if err != nil {
		return "", errors.New("неверный email или пароль")
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password)); err != nil {
		return "", errors.New("неверный email или пароль")
	}

	// Генерация JWT
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id":   user.ID,
		"tenant_id": user.TenantID,
		"exp":       time.Now().Add(time.Hour * 72).Unix(),
	})

	return token.SignedString([]byte(s.secret))
}
