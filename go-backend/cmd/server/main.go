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
	"gorm.io/gorm"
)

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func main() {
	jwtSecret := getEnv("JWT_SECRET", "")
	if jwtSecret == "" {
		jwtSecret = "super_secret_key_123"
		log.Println("ВНИМАНИЕ: JWT_SECRET не задан, используется небезопасный дефолт. Установите переменную окружения JWT_SECRET перед деплоем!")
	}

	// Пути относительно бинарника / рабочей директории
	dbPath := getEnv("DB_PATH", "deskly.db")
	staticDir := getEnv("STATIC_DIR", "frontend/dist")

	gormDB := db.InitDB(dbPath)

	userRepo := repository.NewUserRepo(gormDB)
	authSvc := service.NewAuthService(userRepo, jwtSecret)
	authHandler := handler.NewAuthHandler(authSvc)

	clientRepo := repository.NewClientRepo(gormDB)
	clientSvc := service.NewClientService(clientRepo)
	clientHandler := handler.NewClientHandler(clientSvc, gormDB)

	productRepo := repository.NewProductRepo(gormDB)
	productSvc := service.NewProductService(productRepo)
	productHandler := handler.NewProductHandler(productSvc)

	orderRepo := repository.NewOrderRepo(gormDB)
	orderSvc := service.NewOrderService(orderRepo)
	orderHandler := handler.NewOrderHandler(orderSvc, gormDB)

	dashboardHandler := handler.NewDashboardHandler(gormDB)
	paymentHandler := handler.NewPaymentHandler(gormDB)
	taskRepo := repository.NewTaskRepo(gormDB)
	taskSvc := service.NewTaskService(taskRepo)
	taskHandler := handler.NewTaskHandler(taskSvc)

	// Создаем дефолтного админа, если пользователей нет
	var count int64
	gormDB.Model(&domain.User{}).Count(&count)
	if count == 0 {
		authSvc.Register(1, "admin@deskly.com", "password")
		log.Println("Создан дефолтный пользователь: admin@deskly.com / password")
	}

	// Чистка платежей без заказа (выполняется только при наличии orphan-записей)
	result := gormDB.Exec("DELETE FROM payments WHERE order_id NOT IN (SELECT id FROM orders WHERE deleted_at IS NULL)")
	if result.Error != nil {
		log.Printf("ВНИМАНИЕ: ошибка при очистке платежей: %v", result.Error)
	} else if result.RowsAffected > 0 {
		log.Printf("Удалено %d платежей без привязки к заказу", result.RowsAffected)
	}

	mux := http.NewServeMux()

	// Публичные роуты
	mux.HandleFunc("GET /api/v1/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"status":"ok"}`))
	})
	mux.HandleFunc("POST /api/v1/auth/login", authHandler.Login)

	// Dashboard
	mux.HandleFunc("GET /api/v1/dashboard/stats", dashboardHandler.GetStats)
	mux.HandleFunc("GET /api/v1/dashboard/revenue", dashboardHandler.GetRevenue)

	// Клиенты
	mux.HandleFunc("POST /api/v1/clients", clientHandler.CreateClient)
	mux.HandleFunc("GET /api/v1/clients", clientHandler.ListClients)
	mux.HandleFunc("GET /api/v1/clients/{id}", clientHandler.GetClient)
	mux.HandleFunc("GET /api/v1/clients/{id}/orders", clientHandler.GetClientOrders)
	mux.HandleFunc("PUT /api/v1/clients/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		var c domain.Client
		if err := json.NewDecoder(r.Body).Decode(&c); err != nil {
			http.Error(w, "неверный формат", http.StatusBadRequest)
			return
		}
		gormDB.Model(&domain.Client{}).Where("id = ? AND tenant_id = ?", id, 1).Updates(c)
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("DELETE /api/v1/clients/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		var c domain.Client
		if gormDB.Where("id = ? AND tenant_id = ?", id, 1).First(&c).Error == nil {
			gormDB.Delete(&c)
			handler.LogActivityPub(gormDB, 1, "delete", "client", c.ID, "Клиент удалён: "+c.Name)
		}
		w.WriteHeader(http.StatusNoContent)
	})

	// Товары
	mux.HandleFunc("POST /api/v1/products", productHandler.CreateProduct)
	mux.HandleFunc("GET /api/v1/products", productHandler.ListProducts)
	mux.HandleFunc("PUT /api/v1/products/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		var p domain.Product
		if err := json.NewDecoder(r.Body).Decode(&p); err != nil {
			http.Error(w, "неверный формат", http.StatusBadRequest)
			return
		}
		gormDB.Model(&domain.Product{}).Where("id = ? AND tenant_id = ?", id, 1).Updates(p)
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("PATCH /api/v1/products/{id}/toggle", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		gormDB.Model(&domain.Product{}).Where("id = ?", id).Update("is_active", gorm.Expr("NOT is_active"))
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("DELETE /api/v1/products/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		gormDB.Where("id = ? AND tenant_id = ?", id, 1).Delete(&domain.Product{})
		w.WriteHeader(http.StatusNoContent)
	})

	// Заказы
	mux.HandleFunc("POST /api/v1/orders", orderHandler.CreateOrder)
	mux.HandleFunc("GET /api/v1/orders", orderHandler.ListOrders)
	mux.HandleFunc("GET /api/v1/orders/{id}", orderHandler.GetOrder)
	mux.HandleFunc("PUT /api/v1/orders/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		var o domain.Order
		if err := json.NewDecoder(r.Body).Decode(&o); err != nil {
			http.Error(w, "неверный формат", http.StatusBadRequest)
			return
		}
		gormDB.Model(&domain.Order{}).Where("id = ? AND tenant_id = ?", id, 1).Updates(o)
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("PATCH /api/v1/orders/{id}/status", orderHandler.UpdateStatus)
	mux.HandleFunc("GET /api/v1/orders/{id}/comments", orderHandler.ListComments)
	mux.HandleFunc("POST /api/v1/orders/{id}/comments", orderHandler.CreateComment)
	mux.HandleFunc("DELETE /api/v1/orders/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		var o domain.Order
		if gormDB.Where("id = ? AND tenant_id = ?", id, 1).First(&o).Error == nil {
			gormDB.Where("order_id = ?", id).Delete(&domain.Payment{})
			gormDB.Delete(&o)
			handler.LogActivityPub(gormDB, 1, "delete", "order", o.ID, "Заказ удалён: "+o.Title)
		}
		w.WriteHeader(http.StatusNoContent)
	})

	// Платежи
	mux.HandleFunc("POST /api/v1/payments", paymentHandler.CreatePayment)

	// Лог активности
	mux.HandleFunc("GET /api/v1/activity", func(w http.ResponseWriter, r *http.Request) {
		logs := make([]domain.ActivityLog, 0)
		gormDB.Where("tenant_id = ?", 1).Order("created_at desc").Limit(20).Find(&logs)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(logs)
	})

	// Задачи
	mux.HandleFunc("GET /api/v1/tasks", taskHandler.ListTasks)
	mux.HandleFunc("POST /api/v1/tasks", taskHandler.CreateTask)
	mux.HandleFunc("PUT /api/v1/tasks/{id}", taskHandler.UpdateTask)
	mux.HandleFunc("DELETE /api/v1/tasks/{id}", taskHandler.DeleteTask)

	// SPA раздача статики
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if strings.HasPrefix(r.URL.Path, "/api/") {
			return
		}
		path := filepath.Join(staticDir, r.URL.Path)
		_, err := os.Stat(path)
		if os.IsNotExist(err) || r.URL.Path == "/" {
			http.ServeFile(w, r, filepath.Join(staticDir, "index.html"))
			return
		}
		http.FileServer(http.Dir(staticDir)).ServeHTTP(w, r)
	})

	port := getEnv("PORT", "8080")
	corsOrigin := getEnv("CORS_ORIGIN", "http://localhost:5173")
	wrappedMux := handler.CORSMiddleware(corsOrigin, handler.JWTMiddleware(jwtSecret, mux))
	log.Printf("DesklyCRM запущен на http://localhost:%s", port)
	if err := http.ListenAndServe(":"+port, wrappedMux); err != nil {
		log.Fatal(err)
	}
}
