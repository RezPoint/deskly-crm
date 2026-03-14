package db

import (
	"log"

	"deskly-crm-go/internal/domain"
	"github.com/glebarez/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

func InitDB(dbPath string) *gorm.DB {
	db, err := gorm.Open(sqlite.Open(dbPath), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	if err != nil {
		log.Fatalf("Не удалось подключиться к базе данных: %v", err)
	}

	// Автоматическая миграция
	err = db.AutoMigrate(
		&domain.Tenant{},
		&domain.User{},
		&domain.Client{},
		&domain.Order{},
		&domain.OrderItem{},
		&domain.Payment{},
		&domain.Product{},
		&domain.Task{},
		&domain.ActivityLog{},
	)
	if err != nil {
		log.Fatalf("Ошибка миграции БД: %v", err)
	}

	log.Println("✅ База данных инициализирована и мигрирована")
	return db
}
