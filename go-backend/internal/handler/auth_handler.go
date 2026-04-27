package handler

import (
	"encoding/json"
	"net"
	"net/http"
	"strings"
	"sync"
	"time"

	"deskly-crm-go/internal/service"
)

const (
	rateLimitMax    = 5
	rateLimitWindow = 15 * time.Minute
)

type loginAttempts struct {
	mu         sync.Mutex
	timestamps []time.Time
}

var loginLimiter sync.Map // key: string (IP) → value: *loginAttempts

func getClientIP(r *http.Request) string {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		return strings.TrimSpace(strings.Split(xff, ",")[0])
	}
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return host
}

func checkRateLimit(ip string) bool {
	val, _ := loginLimiter.LoadOrStore(ip, &loginAttempts{})
	attempts := val.(*loginAttempts)
	attempts.mu.Lock()
	defer attempts.mu.Unlock()

	now := time.Now()
	cutoff := now.Add(-rateLimitWindow)

	valid := attempts.timestamps[:0]
	for _, t := range attempts.timestamps {
		if t.After(cutoff) {
			valid = append(valid, t)
		}
	}
	attempts.timestamps = valid

	if len(attempts.timestamps) >= rateLimitMax {
		return false
	}
	attempts.timestamps = append(attempts.timestamps, now)
	return true
}

type AuthHandler struct {
	authSvc service.AuthService
}

func NewAuthHandler(authSvc service.AuthService) *AuthHandler {
	return &AuthHandler{authSvc: authSvc}
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	ip := getClientIP(r)
	if !checkRateLimit(ip) {
		http.Error(w, "слишком много попыток, попробуйте позже", http.StatusTooManyRequests)
		return
	}

	var req struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "неверный формат запроса", http.StatusBadRequest)
		return
	}

	token, err := h.authSvc.Login(req.Email, req.Password)
	if err != nil {
		http.Error(w, err.Error(), http.StatusUnauthorized)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"token": token})
}
