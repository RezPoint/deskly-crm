package handler

import (
	"net/http"
	"strings"

	"github.com/golang-jwt/jwt/v5"
)

func CORSMiddleware(allowedOrigin string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", allowedOrigin)
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// JWTMiddleware проверяет Bearer-токен для всех /api/v1/* роутов кроме /auth/login
func JWTMiddleware(secret string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Пропускаем без проверки: auth эндпоинт и health
		path := r.URL.Path
		if path == "/api/v1/auth/login" || path == "/api/v1/health" {
			next.ServeHTTP(w, r)
			return
		}

		// Только для API маршрутов
		if strings.HasPrefix(path, "/api/") {
			authHeader := r.Header.Get("Authorization")
			if !strings.HasPrefix(authHeader, "Bearer ") {
				http.Error(w, "требуется авторизация", http.StatusUnauthorized)
				return
			}

			tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
			token, err := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
				if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
					return nil, jwt.ErrSignatureInvalid
				}
				return []byte(secret), nil
			})

			if err != nil || !token.Valid {
				http.Error(w, "неверный или просроченный токен", http.StatusUnauthorized)
				return
			}
		}

		next.ServeHTTP(w, r)
	})
}
