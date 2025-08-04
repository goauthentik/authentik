package telemetry

import (
	"context"
	"net/http"
	"time"

	"github.com/gorilla/mux"
	"github.com/sirupsen/logrus"

	"goauthentik.io/internal/config"
)

// Example demonstrates how to integrate telemetry into a Go service
func ExampleIntegration() {
	// 1. Initialize telemetry early in main()
	ctx := context.Background()
	serviceName := "authentik.proxy" // or "authentik.ldap", "authentik.radius", etc.

	err := Initialize(ctx, serviceName)
	if err != nil {
		logrus.WithError(err).Warning("Failed to initialize telemetry")
	}

	// Ensure cleanup on shutdown
	defer func() {
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := Shutdown(shutdownCtx); err != nil {
			logrus.WithError(err).Error("Failed to shutdown telemetry")
		}
	}()

	// 2. Create HTTP router with telemetry middleware
	router := mux.NewRouter()

	// Add telemetry middleware to all routes
	httpMiddleware := NewGlobalHTTPMiddleware(serviceName)
	router.Use(httpMiddleware.Handler)

	// Add your routes
	router.HandleFunc("/api/v1/status", handleStatus).Methods("GET")
	router.HandleFunc("/api/v1/auth", handleAuth).Methods("POST")

	// 3. Start server
	server := &http.Server{
		Addr:    ":8080",
		Handler: router,
	}

	logrus.Info("Starting server with telemetry enabled")
	server.ListenAndServe()
}

// Example HTTP handler with telemetry
func handleStatus(w http.ResponseWriter, r *http.Request) {
	// The middleware automatically creates spans and records metrics
	// You can add custom attributes to the current span
	AddSpanAttribute(r.Context(), "handler.name", "status")

	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "ok"}`))
}

// Example authentication handler with telemetry
func handleAuth(w http.ResponseWriter, r *http.Request) {
	// Create custom span for authentication logic
	ctx, span := StartSpan(r.Context(), "auth.authenticate")
	defer span.End()

	// Use auth middleware for detailed authentication telemetry
	authMiddleware := NewGlobalAuthMiddleware()

	success, err := authMiddleware.RecordAuth(ctx, "password", func() (bool, error) {
		// Your authentication logic here
		username := r.FormValue("username")
		password := r.FormValue("password")

		// Add user context to span
		AddSpanAttribute(ctx, "auth.username", username)

		// Simulate authentication
		if username == "admin" && password == "password" {
			return true, nil
		}
		return false, nil
	})

	if err != nil {
		RecordSpanError(ctx, err)
		http.Error(w, "Authentication error", http.StatusInternalServerError)
		return
	}

	if success {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"authenticated": true}`))
	} else {
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte(`{"authenticated": false}`))
	}
}

// Example LDAP operation with telemetry
func ExampleLDAPOperation(ctx context.Context) error {
	ldapMiddleware := NewGlobalLDAPMiddleware()

	return ldapMiddleware.RecordOperation(ctx, "search", func() error {
		// Add custom span attributes
		AddSpanAttribute(ctx, "ldap.base_dn", "dc=example,dc=com")
		AddSpanAttribute(ctx, "ldap.filter", "(objectClass=user)")

		// Your LDAP search logic here
		time.Sleep(50 * time.Millisecond) // Simulate work

		return nil
	})
}

// Example configuration for different environments
func ExampleConfiguration() {
	// Development environment
	devConfig := &config.Config{
		Telemetry: config.TelemetryConfig{
			OTLP: config.OTLPConfig{
				Enabled:          true,
				Endpoint:         "localhost:4317",
				Protocol:         "grpc",
				TracesSampleRate: 1.0, // 100% sampling in dev
				ServiceName:      "authentik-dev",
			},
		},
	}

	// Production environment
	prodConfig := &config.Config{
		Telemetry: config.TelemetryConfig{
			OTLP: config.OTLPConfig{
				Enabled:          true,
				Endpoint:         "otel-collector.monitoring.svc.cluster.local:4317",
				Protocol:         "grpc",
				TracesSampleRate: 0.05, // 5% sampling in production
				ServiceName:      "authentik",
				ServiceVersion:   "2025.1.0",
				Headers: map[string]string{
					"Authorization": "Bearer your-token",
				},
				ResourceAttributes: map[string]string{
					"deployment.environment": "production",
					"service.namespace":      "authentik",
				},
			},
		},
	}

	// Environment variables override YAML configuration:
	// AUTHENTIK_TELEMETRY__OTLP__ENABLED=true
	// AUTHENTIK_TELEMETRY__OTLP__ENDPOINT=otel-collector:4317
	// AUTHENTIK_TELEMETRY__OTLP__TRACES_SAMPLE_RATE=0.1

	_ = devConfig
	_ = prodConfig
}
