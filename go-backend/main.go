package main

import (
	"encoding/json"
	"log"
	"net/http"
)

// Response - стандартный формат ответа
type Response struct {
	Message string `json:"message"`
	Status  string `json:"status"`
}

func main() {
	// Настраиваем роутер (аналог FastAPI APIRouter)
	mux := http.NewServeMux()

	// Простейший эндпоинт для проверки здоровья сервера
	mux.HandleFunc("GET /api/v1/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		
		response := Response{
			Message: "DesklyCRM Go Server is flying! 🚀",
			Status:  "ok",
		}
		
		json.NewEncoder(w).Encode(response)
	})

	// Запускаем сервер
	log.Println("🚀 Сервер DesklyCRM запущен на http://localhost:8080")
	if err := http.ListenAndServe(":8080", mux); err != nil {
		log.Fatalf("Ошибка запуска сервера: %v", err)
	}
}
