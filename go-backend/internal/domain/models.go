package domain

import (
	"time"

	"github.com/shopspring/decimal"
	"gorm.io/gorm"
)

type BaseEntity struct {
	ID        uint            `gorm:"primaryKey" json:"id"`
	CreatedAt time.Time       `gorm:"index" json:"created_at"`
	UpdatedAt time.Time       `json:"updated_at"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	TenantID  uint            `gorm:"not null;index" json:"tenant_id"`
}

type Tenant struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	Name      string    `gorm:"size:120;not null" json:"name"`
	Slug      string    `gorm:"size:120;not null;uniqueIndex" json:"slug"`
	CreatedAt time.Time `json:"created_at"`
}

type User struct {
	BaseEntity
	Email        string `gorm:"size:200;not null;index" json:"email"`
	PasswordHash string `gorm:"size:255;not null" json:"-"`
	Role         string `gorm:"size:30;not null;default:'owner'" json:"role"`
}

type Client struct {
	BaseEntity
	Name     string `gorm:"size:120;not null" json:"name"`
	Phone    string `gorm:"size:50;index" json:"phone"`
	Telegram string `gorm:"size:80;index" json:"telegram"`
	Notes    string `gorm:"type:text" json:"notes"`
}

type Order struct {
	BaseEntity
	ClientID uint            `gorm:"not null" json:"client_id"`
	Title    string          `gorm:"size:200;not null" json:"title"`
	Price    decimal.Decimal `gorm:"type:numeric(12,2);not null;default:0" json:"price"`
	Status   string          `gorm:"size:30;not null;default:'new'" json:"status"`
	Comment  string          `gorm:"type:text" json:"comment"`
	
	Items    []OrderItem     `gorm:"foreignKey:OrderID" json:"items,omitempty"`
	Payments []Payment       `gorm:"foreignKey:OrderID" json:"payments,omitempty"`
}

type OrderItem struct {
	BaseEntity
	OrderID    uint            `gorm:"not null;index" json:"order_id"`
	Title      string          `gorm:"size:200;not null" json:"title"`
	Quantity   decimal.Decimal `gorm:"type:numeric(12,2);not null;default:1" json:"quantity"`
	UnitPrice  decimal.Decimal `gorm:"type:numeric(12,2);not null;default:0" json:"unit_price"`
	TotalPrice decimal.Decimal `gorm:"type:numeric(12,2);not null;default:0" json:"total_price"`
}

type Payment struct {
	BaseEntity
	OrderID uint            `gorm:"not null;index" json:"order_id"`
	Amount  decimal.Decimal `gorm:"type:numeric(12,2);not null" json:"amount"`
}

type Product struct {
	BaseEntity
	Name        string          `gorm:"size:200;not null;index" json:"name"`
	Description string          `gorm:"type:text" json:"description"`
	Price       decimal.Decimal `gorm:"type:numeric(12,2);not null;default:0" json:"price"`
	IsActive    bool            `gorm:"default:true" json:"is_active"`
}

type Task struct {
	BaseEntity
	OrderID     uint      `gorm:"index" json:"order_id"`
	Title       string    `gorm:"size:300;not null" json:"title"`
	Description string    `gorm:"type:text" json:"description"`
	Status      string    `gorm:"size:30;not null;default:'new'" json:"status"`
	DueDate     *time.Time `gorm:"index" json:"due_date"`
}

type ActivityLog struct {
	BaseEntity
	UserID     uint   `gorm:"index" json:"user_id"`
	Action     string `gorm:"size:50;not null" json:"action"`
	EntityType string `gorm:"size:30;not null" json:"entity_type"`
	EntityID   uint   `json:"entity_id"`
	Message    string `gorm:"size:500" json:"message"`
}
