package telemetry

import (
	"context"
	"testing"
	"time"

	"github.com/sirupsen/logrus"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"goauthentik.io/internal/config"
)

func TestNewProvider(t *testing.T) {
	cfg := &config.Config{
		Telemetry: config.TelemetryConfig{
			OTLP: config.OTLPConfig{
				Enabled:          false,
				ServiceName:      "test-service",
				TracesSampleRate: 0.1,
			},
		},
	}
	logger := logrus.New()

	provider := NewProvider(cfg, logger)
	assert.NotNil(t, provider)
	assert.False(t, provider.IsEnabled())
}

func TestProviderDisabled(t *testing.T) {
	cfg := &config.Config{
		Telemetry: config.TelemetryConfig{
			OTLP: config.OTLPConfig{
				Enabled: false,
			},
		},
	}
	logger := logrus.New()

	provider := NewProvider(cfg, logger)
	require.NotNil(t, provider)

	ctx := context.Background()
	err := provider.Initialize(ctx, "test-service")
	assert.NoError(t, err)
	assert.False(t, provider.initialized)
}

func TestProviderWithoutEndpoint(t *testing.T) {
	cfg := &config.Config{
		Telemetry: config.TelemetryConfig{
			OTLP: config.OTLPConfig{
				Enabled:          true,
				Endpoint:         "", // No endpoint
				ServiceName:      "test-service",
				TracesSampleRate: 0.1,
			},
		},
	}
	logger := logrus.New()

	provider := NewProvider(cfg, logger)
	require.NotNil(t, provider)

	ctx := context.Background()
	err := provider.Initialize(ctx, "test-service")
	assert.NoError(t, err)
	assert.True(t, provider.initialized)
}

func TestAdaptiveSampler(t *testing.T) {
	sampler := NewAdaptiveSampler(0.1, 1.0)
	assert.NotNil(t, sampler)
	assert.Equal(t, "AdaptiveSampler", sampler.Description())

	// Test health check exclusion (mock parameters)
	// Note: In real tests, you'd create proper SamplingParameters
	assert.NotNil(t, sampler.healthCheckPatterns)
	assert.Len(t, sampler.healthCheckPatterns, 4)
}

func TestHTTPMiddleware(t *testing.T) {
	cfg := &config.Config{
		Telemetry: config.TelemetryConfig{
			OTLP: config.OTLPConfig{
				Enabled: false,
			},
		},
	}
	logger := logrus.New()
	provider := NewProvider(cfg, logger)

	middleware := NewHTTPMiddleware(provider, "test-service")
	assert.NotNil(t, middleware)
	assert.Equal(t, "test-service", middleware.serviceName)

	// Test path exclusion
	assert.True(t, middleware.shouldExclude("/-/health/"))
	assert.True(t, middleware.shouldExclude("/-/metrics/"))
	assert.True(t, middleware.shouldExclude("/static/test.js"))
	assert.False(t, middleware.shouldExclude("/api/v3/users/"))
}

func TestLDAPMiddleware(t *testing.T) {
	cfg := &config.Config{
		Telemetry: config.TelemetryConfig{
			OTLP: config.OTLPConfig{
				Enabled: false,
			},
		},
	}
	logger := logrus.New()
	provider := NewProvider(cfg, logger)

	middleware := NewLDAPMiddleware(provider)
	assert.NotNil(t, middleware)

	// Test operation recording with disabled telemetry
	ctx := context.Background()
	callCount := 0
	err := middleware.RecordOperation(ctx, "search", func() error {
		callCount++
		return nil
	})

	assert.NoError(t, err)
	assert.Equal(t, 1, callCount)
}

func TestAuthMiddleware(t *testing.T) {
	cfg := &config.Config{
		Telemetry: config.TelemetryConfig{
			OTLP: config.OTLPConfig{
				Enabled: false,
			},
		},
	}
	logger := logrus.New()
	provider := NewProvider(cfg, logger)

	middleware := NewAuthMiddleware(provider)
	assert.NotNil(t, middleware)

	// Test auth recording with disabled telemetry
	ctx := context.Background()
	callCount := 0
	success, err := middleware.RecordAuth(ctx, "password", func() (bool, error) {
		callCount++
		return true, nil
	})

	assert.NoError(t, err)
	assert.True(t, success)
	assert.Equal(t, 1, callCount)
}

func TestGlobalFunctions(t *testing.T) {
	// Test when no global provider is set
	assert.False(t, IsEnabled())
	assert.NotNil(t, GetTracer("test"))
	assert.NotNil(t, GetMeter("test"))

	// These should not panic when provider is nil
	ctx := context.Background()
	RecordRequest(ctx, "GET", "200", 0.1)
	RecordAuth(ctx, "password", true)
	RecordLDAPOperation(ctx, "search", 0.1, true)

	assert.NoError(t, Shutdown(ctx))
}

func TestProviderShutdown(t *testing.T) {
	cfg := &config.Config{
		Telemetry: config.TelemetryConfig{
			OTLP: config.OTLPConfig{
				Enabled: false,
			},
		},
	}
	logger := logrus.New()
	provider := NewProvider(cfg, logger)

	ctx := context.Background()
	err := provider.Shutdown(ctx)
	assert.NoError(t, err)
}

func TestMetricsRecording(t *testing.T) {
	cfg := &config.Config{
		Telemetry: config.TelemetryConfig{
			OTLP: config.OTLPConfig{
				Enabled: false, // Disabled, so metrics should be no-op
			},
		},
	}
	logger := logrus.New()
	provider := NewProvider(cfg, logger)

	ctx := context.Background()

	// These should not panic even when telemetry is disabled
	provider.RecordRequest(ctx, "GET", "200", 0.5)
	provider.RecordAuth(ctx, "password", true)
	provider.RecordLDAPOperation(ctx, "search", 0.2, true)
}

func TestSpanUtilities(t *testing.T) {
	ctx := context.Background()

	// Test span utilities with no provider
	ctx2, span := StartSpan(ctx, "test-operation")
	assert.NotNil(t, ctx2)
	assert.NotNil(t, span)
	span.End()

	// Test context utilities
	ctx3, cancel := WithTimeout(ctx, time.Second)
	assert.NotNil(t, ctx3)
	assert.NotNil(t, cancel)
	cancel()

	ctx4, cancel2 := WithCancel(ctx)
	assert.NotNil(t, ctx4)
	assert.NotNil(t, cancel2)
	cancel2()

	// These should not panic
	AddSpanAttribute(ctx, "test.key", "test.value")
	RecordSpanError(ctx, assert.AnError)
}
