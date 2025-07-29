package telemetry

import (
	"context"
	"net/http"
	"regexp"
	"strconv"
	"time"

	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

// HTTPMiddleware provides OpenTelemetry instrumentation for HTTP handlers
type HTTPMiddleware struct {
	provider         *Provider
	excludedPatterns []*regexp.Regexp
	serviceName      string
}

// NewHTTPMiddleware creates a new HTTP middleware with telemetry
func NewHTTPMiddleware(provider *Provider, serviceName string) *HTTPMiddleware {
	return &HTTPMiddleware{
		provider:    provider,
		serviceName: serviceName,
		excludedPatterns: []*regexp.Regexp{
			regexp.MustCompile(`/-/health/?$`),
			regexp.MustCompile(`/-/metrics/?$`),
			regexp.MustCompile(`/-/ready/?$`),
			regexp.MustCompile(`/-/live/?$`),
			regexp.MustCompile(`/static/.*`),
			regexp.MustCompile(`/favicon\.ico$`),
		},
	}
}

// Handler wraps an HTTP handler with OpenTelemetry instrumentation
func (m *HTTPMiddleware) Handler(next http.Handler) http.Handler {
	if !m.provider.IsEnabled() {
		return next
	}

	// Use otelhttp for automatic instrumentation
	return otelhttp.NewHandler(
		http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip excluded paths
			if m.shouldExclude(r.URL.Path) {
				next.ServeHTTP(w, r)
				return
			}

			// Add custom span attributes
			span := trace.SpanFromContext(r.Context())
			m.setSpanAttributes(span, r)

			// Record request start time
			start := time.Now()

			// Create response writer wrapper to capture status code
			rw := &responseWriter{ResponseWriter: w, statusCode: 200}

			// Process request
			next.ServeHTTP(rw, r)

			// Record metrics
			duration := time.Since(start).Seconds()
			status := strconv.Itoa(rw.statusCode)

			m.provider.RecordRequest(r.Context(), r.Method, status, duration)

			// Set span status for errors
			if rw.statusCode >= 400 {
				span.SetAttributes(attribute.Int("http.status_code", rw.statusCode))
				if rw.statusCode >= 500 {
					span.RecordError(nil, trace.WithAttributes(
						attribute.String("error.type", "http_server_error"),
						attribute.String("error.message", http.StatusText(rw.statusCode)),
					))
				}
			}
		}),
		"http.request",
		otelhttp.WithSpanNameFormatter(m.getSpanName),
	)
}

// HandlerFunc wraps an HTTP handler function with OpenTelemetry instrumentation
func (m *HTTPMiddleware) HandlerFunc(next http.HandlerFunc) http.Handler {
	return m.Handler(next)
}

// shouldExclude checks if a request path should be excluded from tracing
func (m *HTTPMiddleware) shouldExclude(path string) bool {
	for _, pattern := range m.excludedPatterns {
		if pattern.MatchString(path) {
			return true
		}
	}
	return false
}

// setSpanAttributes sets custom attributes on the span
func (m *HTTPMiddleware) setSpanAttributes(span trace.Span, r *http.Request) {
	if span == nil || !span.IsRecording() {
		return
	}

	// Set service-specific attributes
	span.SetAttributes(
		attribute.String("service.name", m.serviceName),
		attribute.String("http.method", r.Method),
		attribute.String("http.url", r.URL.String()),
		attribute.String("http.scheme", r.URL.Scheme),
		attribute.String("http.host", r.Host),
		attribute.String("http.target", r.URL.Path),
	)

	// User agent
	if userAgent := r.Header.Get("User-Agent"); userAgent != "" {
		span.SetAttributes(attribute.String("http.user_agent", userAgent))
	}

	// Client IP
	if clientIP := getClientIP(r); clientIP != "" {
		span.SetAttributes(attribute.String("http.client_ip", clientIP))
	}

	// Content length
	if r.ContentLength > 0 {
		span.SetAttributes(attribute.Int64("http.request_content_length", r.ContentLength))
	}
}

// getSpanName generates a span name for the request
func (m *HTTPMiddleware) getSpanName(operation string, r *http.Request) string {
	method := r.Method
	path := r.URL.Path

	// Simplify common API patterns
	if path == "/" {
		return method + " /"
	}

	// For outpost endpoints, use generic names
	switch {
	case regexp.MustCompile(`^/outpost\.goauthentik\.io/`).MatchString(path):
		return method + " /outpost.goauthentik.io/*"
	case regexp.MustCompile(`^/akprox/`).MatchString(path):
		return method + " /akprox/*"
	case regexp.MustCompile(`^/api/`).MatchString(path):
		return method + " /api/*"
	default:
		return method + " " + path
	}
}

// getClientIP extracts the client IP from the request
func getClientIP(r *http.Request) string {
	// Check X-Forwarded-For header
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		return xff
	}

	// Check X-Real-IP header
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return xri
	}

	// Fall back to RemoteAddr
	return r.RemoteAddr
}

// responseWriter wraps http.ResponseWriter to capture the status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

// WriteHeader captures the status code
func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Write ensures WriteHeader is called
func (rw *responseWriter) Write(b []byte) (int, error) {
	if rw.statusCode == 0 {
		rw.statusCode = 200
	}
	return rw.ResponseWriter.Write(b)
}

// LDAPMiddleware provides telemetry for LDAP operations
type LDAPMiddleware struct {
	provider *Provider
}

// NewLDAPMiddleware creates a new LDAP middleware with telemetry
func NewLDAPMiddleware(provider *Provider) *LDAPMiddleware {
	return &LDAPMiddleware{
		provider: provider,
	}
}

// RecordOperation records an LDAP operation with telemetry
func (m *LDAPMiddleware) RecordOperation(ctx context.Context, operation string, fn func() error) error {
	if !m.provider.IsEnabled() {
		return fn()
	}

	// Start tracing span
	tracer := m.provider.GetTracer("authentik.ldap")
	ctx, span := tracer.Start(ctx, "ldap."+operation)
	defer span.End()

	// Set span attributes
	span.SetAttributes(
		attribute.String("ldap.operation", operation),
	)

	// Record operation start time
	start := time.Now()

	// Execute operation
	err := fn()

	// Record metrics
	duration := time.Since(start).Seconds()
	success := err == nil

	m.provider.RecordLDAPOperation(ctx, operation, duration, success)

	// Record error if any
	if err != nil {
		span.RecordError(err)
		span.SetAttributes(attribute.Bool("error", true))
	}

	return err
}

// AuthMiddleware provides telemetry for authentication operations
type AuthMiddleware struct {
	provider *Provider
}

// NewAuthMiddleware creates a new authentication middleware with telemetry
func NewAuthMiddleware(provider *Provider) *AuthMiddleware {
	return &AuthMiddleware{
		provider: provider,
	}
}

// RecordAuth records an authentication attempt with telemetry
func (m *AuthMiddleware) RecordAuth(ctx context.Context, method string, fn func() (bool, error)) (bool, error) {
	if !m.provider.IsEnabled() {
		return fn()
	}

	// Start tracing span
	tracer := m.provider.GetTracer("authentik.auth")
	ctx, span := tracer.Start(ctx, "auth."+method)
	defer span.End()

	// Set span attributes
	span.SetAttributes(
		attribute.String("auth.method", method),
	)

	// Execute authentication
	success, err := fn()

	// Record metrics
	m.provider.RecordAuth(ctx, method, success)

	// Set span attributes based on result
	span.SetAttributes(
		attribute.Bool("auth.success", success),
	)

	// Record error if any
	if err != nil {
		span.RecordError(err)
		span.SetAttributes(attribute.Bool("error", true))
	}

	return success, err
}
