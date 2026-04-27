package handler

import (
	"deskly-crm-go/internal/domain"
	"gorm.io/gorm"
)

func logActivity(db *gorm.DB, tenantID uint, action, entityType string, entityID uint, message string) {
	db.Create(&domain.ActivityLog{
		BaseEntity: domain.BaseEntity{TenantID: tenantID},
		Action:     action,
		EntityType: entityType,
		EntityID:   entityID,
		Message:    message,
	})
}

// LogActivityPub — экспортированная версия для использования в main.go
func LogActivityPub(db *gorm.DB, tenantID uint, action, entityType string, entityID uint, message string) {
	logActivity(db, tenantID, action, entityType, entityID, message)
}
