package handler

import (
	"encoding/json"
	"net/http"
	"strconv"

	"deskly-crm-go/internal/service"
)

type ClientHandler struct {
	svc service.ClientService
}

func NewClientHandler(svc service.ClientService) *ClientHandler {
	return &ClientHandler{svc: svc}
}

func (h *ClientHandler) CreateClient(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Name     string `json:"name"`
		Phone    string `json:"phone"`
		Telegram string `json:"telegram"`
		Notes    string `json:"notes"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Ошибка парсинга JSON", http.StatusBadRequest)
		return
	}

	client, err := h.svc.CreateClient(1, req.Name, req.Phone, req.Telegram, req.Notes)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(client)
}

func (h *ClientHandler) ListClients(w http.ResponseWriter, r *http.Request) {
	clients, err := h.svc.ListClients(1)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(clients)
}

func (h *ClientHandler) GetClient(w http.ResponseWriter, r *http.Request) {
	idStr := r.PathValue("id")
	id, _ := strconv.ParseUint(idStr, 10, 32)

	client, err := h.svc.GetClient(uint(id), 1)
	if err != nil {
		http.Error(w, "Клиент не найден", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(client)
}
