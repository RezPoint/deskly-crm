package handler

import (
	"encoding/json"
	"net/http"
	"strconv"

	"deskly-crm-go/internal/service"
)

type TaskHandler struct {
	svc service.TaskService
}

func NewTaskHandler(svc service.TaskService) *TaskHandler {
	return &TaskHandler{svc: svc}
}

type taskRequest struct {
	Title       string  `json:"title"`
	Description string  `json:"description"`
	Status      string  `json:"status"`
	OrderID     *uint   `json:"order_id"`
	ClientID    *uint   `json:"client_id"`
	DueDate     *string `json:"due_date"`
}

func (h *TaskHandler) ListTasks(w http.ResponseWriter, r *http.Request) {
	status := r.URL.Query().Get("status")
	orderID := r.URL.Query().Get("order_id")
	tasks, err := h.svc.ListTasks(1, status, orderID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(tasks)
}

func (h *TaskHandler) CreateTask(w http.ResponseWriter, r *http.Request) {
	var req taskRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "неверный формат", http.StatusBadRequest)
		return
	}
	var orderID, clientID uint
	if req.OrderID != nil {
		orderID = *req.OrderID
	}
	if req.ClientID != nil {
		clientID = *req.ClientID
	}
	task, err := h.svc.CreateTask(1, req.Title, req.Description, orderID, clientID, req.DueDate)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(task)
}

func (h *TaskHandler) UpdateTask(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseUint(r.PathValue("id"), 10, 32)
	if err != nil {
		http.Error(w, "неверный id", http.StatusBadRequest)
		return
	}
	var req taskRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "неверный формат", http.StatusBadRequest)
		return
	}
	var clientID uint
	if req.ClientID != nil {
		clientID = *req.ClientID
	}
	if err := h.svc.UpdateTask(uint(id), 1, req.Title, req.Description, req.Status, clientID, req.DueDate); err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (h *TaskHandler) DeleteTask(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseUint(r.PathValue("id"), 10, 32)
	if err != nil {
		http.Error(w, "неверный id", http.StatusBadRequest)
		return
	}
	h.svc.DeleteTask(uint(id), 1)
	w.WriteHeader(http.StatusNoContent)
}
