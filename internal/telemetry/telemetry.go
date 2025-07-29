// Package telemetry provides OpenTelemetry integration for authentik Go services
package telemetry

import (
	"context"
	"time"

	"github.com/sirupsen/logrus"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/metric"
	"go.opentelemetry.io/otel/metric/noop"
	"go.opentelemetry.io/otel/trace"

	"goauthentik.io/internal/config"
)

// Global provider instance
var globalProvider *Provider

// Initialize sets up OpenTelemetry telemetry with OTLP configuration
func Initialize(ctx context.Context, serviceName string) error {
	cfg := config.Get()
	logger := logrus.StandardLogger()

	globalProvider = NewProvider(cfg, logger)
	return globalProvider.Initialize(ctx, serviceName)
}

// IsEnabled checks if telemetry is enabled
func IsEnabled() bool {
	if globalProvider == nil {
		return false
	}
	return globalProvider.IsEnabled()
}

// GetTracer returns a tracer for the given name
func GetTracer(name string) trace.Tracer {
	if globalProvider == nil {
		return trace.NewNoopTracerProvider().Tracer(name)
	}
	return globalProvider.GetTracer(name)
}

// GetMeter returns a meter for the given name
func GetMeter(name string) metric.Meter {
	if globalProvider == nil {
		return noop.NewMeterProvider().Meter(name)
	}
	return globalProvider.GetMeter(name)
}

// RecordRequest records HTTP request metrics
func RecordRequest(ctx context.Context, method, status string, duration float64) {
	if globalProvider != nil {
		globalProvider.RecordRequest(ctx, method, status, duration)
	}
}

// RecordAuth records authentication metrics
func RecordAuth(ctx context.Context, method string, success bool) {
	if globalProvider != nil {
		globalProvider.RecordAuth(ctx, method, success)
	}
}

// RecordLDAPOperation records LDAP operation metrics
func RecordLDAPOperation(ctx context.Context, operation string, duration float64, success bool) {
	if globalProvider != nil {
		globalProvider.RecordLDAPOperation(ctx, operation, duration, success)
	}
}

// Shutdown gracefully shuts down the telemetry provider
func Shutdown(ctx context.Context) error {
	if globalProvider == nil {
		return nil
	}
	return globalProvider.Shutdown(ctx)
}

// NewGlobalHTTPMiddleware creates HTTP middleware with the global provider
func NewGlobalHTTPMiddleware(serviceName string) *HTTPMiddleware {
	if globalProvider == nil {
		// Return a no-op middleware
		return &HTTPMiddleware{}
	}
	return NewHTTPMiddleware(globalProvider, serviceName)
}

// NewGlobalLDAPMiddleware creates LDAP middleware with the global provider
func NewGlobalLDAPMiddleware() *LDAPMiddleware {
	if globalProvider == nil {
		// Return a no-op middleware
		return &LDAPMiddleware{}
	}
	return NewLDAPMiddleware(globalProvider)
}

// NewGlobalAuthMiddleware creates authentication middleware with the global provider
func NewGlobalAuthMiddleware() *AuthMiddleware {
	if globalProvider == nil {
		// Return a no-op middleware
		return &AuthMiddleware{}
	}
	return NewAuthMiddleware(globalProvider)
}

// StartSpan starts a new span with the global tracer
func StartSpan(ctx context.Context, operationName string) (context.Context, trace.Span) {
	tracer := GetTracer("authentik.outpost")
	return tracer.Start(ctx, operationName)
}

// WithTimeout creates a context with timeout and ensures telemetry cleanup
func WithTimeout(parent context.Context, duration time.Duration) (context.Context, context.CancelFunc) {
	return context.WithTimeout(parent, duration)
}

// WithCancel creates a context with cancel and ensures telemetry cleanup
func WithCancel(parent context.Context) (context.Context, context.CancelFunc) {
	return context.WithCancel(parent)
}

// AddSpanAttribute adds an attribute to the current span if one exists
func AddSpanAttribute(ctx context.Context, key, value string) {
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() {
		span.SetAttributes(attribute.String(key, value))
	}
}

// RecordSpanError records an error on the current span if one exists
func RecordSpanError(ctx context.Context, err error) {
	span := trace.SpanFromContext(ctx)
	if span != nil && span.IsRecording() && err != nil {
		span.RecordError(err)
	}
}
