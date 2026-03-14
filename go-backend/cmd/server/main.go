package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"deskly-crm-go/internal/db"
	"deskly-crm-go/internal/domain"
	"deskly-crm-go/internal/handler"
	"deskly-crm-go/internal/repository"
	"deskly-crm-go/internal/service"
)

func main() {
	gormDB := db.InitDB("C:/github/deskly-crm/go-backend/deskly.db")

	userRepo := repository.NewUserRepo(gormDB)
	authSvc := service.NewAuthService(userRepo, "super_secret_key_123")
	
	clientRepo := repository.NewClientRepo(gormDB)
	clientSvc := service.NewClientService(clientRepo)
	clientHandler := handler.NewClientHandler(clientSvc)

	productRepo := repository.NewProductRepo(gormDB)
	productSvc := service.NewProductService(productRepo)
	productHandler := handler.NewProductHandler(productSvc)

	orderRepo := repository.NewOrderRepo(gormDB)
	orderSvc := service.NewOrderService(orderRepo)
	orderHandler := handler.NewOrderHandler(orderSvc, gormDB)

	dashboardHandler := handler.NewDashboardHandler(gormDB)
	paymentHandler := handler.NewPaymentHandler(gormDB)

	// Создаем тестового админа, если его нет
	var count int64
	gormDB.Model(&domain.User{}).Count(&count)
	if count == 0 {
		authSvc.Register(1, "admin@deskly.com", "password")
	}

	// Разовая чистка платежей от удаленных заказов
	log.Println("🧹 Очистка «сиротских» платежей (включая мягко удаленные)...")
	gormDB.Exec("DELETE FROM payments WHERE order_id NOT IN (SELECT id FROM orders WHERE deleted_at IS NULL)")

	mux := http.NewServeMux()

	// API
	mux.HandleFunc("GET /api/v1/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"ok"}`))
	})
	mux.HandleFunc("GET /api/v1/dashboard/stats", dashboardHandler.GetStats)

	// Роуты клиентов
	mux.HandleFunc("POST /api/v1/clients", clientHandler.CreateClient)
	mux.HandleFunc("GET /api/v1/clients", clientHandler.ListClients)
	mux.HandleFunc("PUT /api/v1/clients/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		var c domain.Client
		json.NewDecoder(r.Body).Decode(&c)
		gormDB.Model(&domain.Client{}).Where("id = ? AND tenant_id = ?", id, 1).Updates(c)
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("DELETE /api/v1/clients/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id"); gormDB.Where("id = ? AND tenant_id = ?", id, 1).Delete(&domain.Client{}); w.WriteHeader(http.StatusNoContent)
	})

	// Роуты товаров
	mux.HandleFunc("POST /api/v1/products", productHandler.CreateProduct)
	mux.HandleFunc("GET /api/v1/products", productHandler.ListProducts)
	mux.HandleFunc("PUT /api/v1/products/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		var p domain.Product
		json.NewDecoder(r.Body).Decode(&p)
		gormDB.Model(&domain.Product{}).Where("id = ? AND tenant_id = ?", id, 1).Updates(p)
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("PATCH /api/v1/products/{id}/toggle", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		var p domain.Product
		if err := gormDB.First(&p, id).Error; err == nil {
			gormDB.Model(&p).Update("is_active", !p.IsActive)
		}
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("DELETE /api/v1/products/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id"); gormDB.Where("id = ? AND tenant_id = ?", id, 1).Delete(&domain.Product{}); w.WriteHeader(http.StatusNoContent)
	})

	// Роуты заказов
	mux.HandleFunc("POST /api/v1/payments", paymentHandler.CreatePayment)
	mux.HandleFunc("POST /api/v1/orders", orderHandler.CreateOrder)
	mux.HandleFunc("GET /api/v1/orders", orderHandler.ListOrders)
	mux.HandleFunc("PUT /api/v1/orders/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		var o domain.Order
		json.NewDecoder(r.Body).Decode(&o)
		gormDB.Model(&domain.Order{}).Where("id = ? AND tenant_id = ?", id, 1).Updates(o)
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("PATCH /api/v1/orders/{id}/status", orderHandler.UpdateStatus)
	mux.HandleFunc("DELETE /api/v1/orders/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		// Сначала удаляем платежи этого заказа
		gormDB.Where("order_id = ?", id).Delete(&domain.Payment{})
		// Затем удаляем сам заказ
		gormDB.Where("id = ? AND tenant_id = ?", id, 1).Delete(&domain.Order{})
		w.WriteHeader(http.StatusNoContent)
	})

	// Умная раздача статики для SPA
	staticDir := "C:/github/deskly-crm/go-backend/frontend/dist"
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if strings.HasPrefix(r.URL.Path, "/api/") { return }
		path := filepath.Join(staticDir, r.URL.Path)
		_, err := os.Stat(path)
		if os.IsNotExist(err) || r.URL.Path == "/" {
			http.ServeFile(w, r, filepath.Join(staticDir, "index.html"))
			return
		}
		http.FileServer(http.Dir(staticDir)).ServeHTTP(w, r)
	})

	wrappedMux := handler.CORSMiddleware(mux)
	log.Println("🚀 DesklyCRM запущен на http://localhost:8080")
	http.ListenAndServe(":8080", wrappedMux)
}
