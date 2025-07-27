package telemetry

import (
	"context"
	"fmt"
	"regexp"
	"time"

	"github.com/sirupsen/logrus"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc"
	"go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/metric"
	"go.opentelemetry.io/otel/metric/noop"
	"go.opentelemetry.io/otel/propagation"
	metricSdk "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	traceSdk "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.20.0"
	"go.opentelemetry.io/otel/trace"

	"goauthentik.io/internal/config"
)

// Provider manages OpenTelemetry telemetry configuration for Go services
type Provider struct {
	config         *config.Config
	logger         *logrus.Logger
	initialized    bool
	tracerProvider *traceSdk.TracerProvider
	meterProvider  *metricSdk.MeterProvider
	sampler        *AdaptiveSampler

	// Metrics
	requestCounter  metric.Int64Counter
	requestDuration metric.Float64Histogram
	authCounter     metric.Int64Counter
	ldapOpCounter   metric.Int64Counter
	ldapOpDuration  metric.Float64Histogram
}

// AdaptiveSampler provides intelligent sampling for Go services
type AdaptiveSampler struct {
	defaultRate         float64
	errorRate           float64
	healthCheckPatterns []*regexp.Regexp
}

// NewAdaptiveSampler creates a new adaptive sampler
func NewAdaptiveSampler(defaultRate, errorRate float64) *AdaptiveSampler {
	return &AdaptiveSampler{
		defaultRate: defaultRate,
		errorRate:   errorRate,
		healthCheckPatterns: []*regexp.Regexp{
			regexp.MustCompile(`/-/health/?$`),
			regexp.MustCompile(`/-/metrics/?$`),
			regexp.MustCompile(`/-/ready/?$`),
			regexp.MustCompile(`/-/live/?$`),
		},
	}
}

// ShouldSample implements custom sampling logic
func (s *AdaptiveSampler) ShouldSample(parameters traceSdk.SamplingParameters) traceSdk.SamplingResult {
	// Extract URL path from span attributes
	var urlPath string
	for _, attr := range parameters.Attributes {
		if attr.Key == "http.target" {
			urlPath = attr.Value.AsString()
			break
		}
	}

	// Never sample health check endpoints
	for _, pattern := range s.healthCheckPatterns {
		if pattern.MatchString(urlPath) {
			return traceSdk.SamplingResult{
				Decision: traceSdk.Drop,
			}
		}
	}

	// For now, sample everything else (can be enhanced with error detection)
	return traceSdk.SamplingResult{
		Decision: traceSdk.RecordAndSample,
	}
}

// Description returns sampler description
func (s *AdaptiveSampler) Description() string {
	return "AdaptiveSampler"
}

// NewProvider creates a new telemetry provider
func NewProvider(cfg *config.Config, logger *logrus.Logger) *Provider {
	return &Provider{
		config:  cfg,
		logger:  logger,
		sampler: NewAdaptiveSampler(cfg.Telemetry.OTLP.TracesSampleRate, 1.0),
	}
}

// IsEnabled checks if telemetry is enabled
func (p *Provider) IsEnabled() bool {
	return p.config.Telemetry.OTLP.Enabled
}

// Initialize sets up OpenTelemetry with OTLP configuration
func (p *Provider) Initialize(ctx context.Context, serviceName string) error {
	if p.initialized {
		return nil
	}

	if !p.IsEnabled() {
		p.logger.Debug("OTLP telemetry disabled")
		return nil
	}

	// Create resource with service attributes
	res, err := p.createResource(serviceName)
	if err != nil {
		return fmt.Errorf("failed to create resource: %w", err)
	}

	// Initialize tracing
	if err := p.setupTracing(ctx, res); err != nil {
		return fmt.Errorf("failed to setup tracing: %w", err)
	}

	// Initialize metrics
	if err := p.setupMetrics(ctx, res); err != nil {
		return fmt.Errorf("failed to setup metrics: %w", err)
	}

	// Set global propagator
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))

	// Create application metrics
	if err := p.createMetrics(); err != nil {
		return fmt.Errorf("failed to create metrics: %w", err)
	}

	p.initialized = true
	p.logger.Info("OpenTelemetry telemetry initialized successfully")
	return nil
}

// createResource creates OpenTelemetry resource with service attributes
func (p *Provider) createResource(serviceName string) (*resource.Resource, error) {
	attrs := []attribute.KeyValue{
		semconv.ServiceName(p.getServiceName(serviceName)),
		semconv.ServiceVersion(p.getServiceVersion()),
	}

	// Add custom resource attributes
	for key, value := range p.config.Telemetry.OTLP.ResourceAttributes {
		attrs = append(attrs, attribute.String(key, value))
	}

	return resource.NewWithAttributes(
		semconv.SchemaURL,
		attrs...,
	), nil
}

// setupTracing configures OpenTelemetry tracing
func (p *Provider) setupTracing(ctx context.Context, res *resource.Resource) error {
	endpoint := p.config.Telemetry.OTLP.Endpoint
	if endpoint == "" {
		return nil
	}

	var exporter traceSdk.SpanExporter
	var err error

	// Create appropriate exporter based on protocol
	if p.config.Telemetry.OTLP.Protocol == "http" {
		opts := []otlptracehttp.Option{
			otlptracehttp.WithEndpoint(endpoint + "/v1/traces"),
		}
		if len(p.config.Telemetry.OTLP.Headers) > 0 {
			opts = append(opts, otlptracehttp.WithHeaders(p.config.Telemetry.OTLP.Headers))
		}
		exporter, err = otlptracehttp.New(ctx, opts...)
	} else {
		// Default to gRPC
		opts := []otlptracegrpc.Option{
			otlptracegrpc.WithEndpoint(endpoint),
		}
		if len(p.config.Telemetry.OTLP.Headers) > 0 {
			opts = append(opts, otlptracegrpc.WithHeaders(p.config.Telemetry.OTLP.Headers))
		}
		exporter, err = otlptracegrpc.New(ctx, opts...)
	}

	if err != nil {
		return fmt.Errorf("failed to create trace exporter: %w", err)
	}

	// Create tracer provider with custom sampler
	p.tracerProvider = traceSdk.NewTracerProvider(
		traceSdk.WithBatcher(exporter),
		traceSdk.WithResource(res),
		traceSdk.WithSampler(p.sampler),
	)

	// Set global tracer provider
	otel.SetTracerProvider(p.tracerProvider)

	return nil
}

// setupMetrics configures OpenTelemetry metrics
func (p *Provider) setupMetrics(ctx context.Context, res *resource.Resource) error {
	endpoint := p.config.Telemetry.OTLP.Endpoint
	if endpoint == "" {
		return nil
	}

	var exporter metricSdk.Exporter
	var err error

	// Create appropriate exporter based on protocol
	if p.config.Telemetry.OTLP.Protocol == "http" {
		opts := []otlpmetrichttp.Option{
			otlpmetrichttp.WithEndpoint(endpoint + "/v1/metrics"),
		}
		if len(p.config.Telemetry.OTLP.Headers) > 0 {
			opts = append(opts, otlpmetrichttp.WithHeaders(p.config.Telemetry.OTLP.Headers))
		}
		exporter, err = otlpmetrichttp.New(ctx, opts...)
	} else {
		// Default to gRPC
		opts := []otlpmetricgrpc.Option{
			otlpmetricgrpc.WithEndpoint(endpoint),
		}
		if len(p.config.Telemetry.OTLP.Headers) > 0 {
			opts = append(opts, otlpmetricgrpc.WithHeaders(p.config.Telemetry.OTLP.Headers))
		}
		exporter, err = otlpmetricgrpc.New(ctx, opts...)
	}

	if err != nil {
		return fmt.Errorf("failed to create metrics exporter: %w", err)
	}

	// Create meter provider
	p.meterProvider = metricSdk.NewMeterProvider(
		metricSdk.WithResource(res),
		metricSdk.WithReader(metricSdk.NewPeriodicReader(exporter,
			metricSdk.WithInterval(60*time.Second),
		)),
	)

	// Set global meter provider
	otel.SetMeterProvider(p.meterProvider)

	return nil
}

// createMetrics creates application-specific metrics
func (p *Provider) createMetrics() error {
	meter := otel.Meter("authentik.outpost")

	var err error

	// HTTP request metrics
	p.requestCounter, err = meter.Int64Counter(
		"authentik_requests_total",
		metric.WithDescription("Total number of HTTP requests"),
	)
	if err != nil {
		return fmt.Errorf("failed to create request counter: %w", err)
	}

	p.requestDuration, err = meter.Float64Histogram(
		"authentik_request_duration_seconds",
		metric.WithDescription("Duration of HTTP requests"),
		metric.WithUnit("s"),
	)
	if err != nil {
		return fmt.Errorf("failed to create request duration histogram: %w", err)
	}

	// Authentication metrics
	p.authCounter, err = meter.Int64Counter(
		"authentik_authentication_total",
		metric.WithDescription("Total number of authentication attempts"),
	)
	if err != nil {
		return fmt.Errorf("failed to create auth counter: %w", err)
	}

	// LDAP-specific metrics
	p.ldapOpCounter, err = meter.Int64Counter(
		"authentik_ldap_operations_total",
		metric.WithDescription("Total number of LDAP operations"),
	)
	if err != nil {
		return fmt.Errorf("failed to create LDAP operation counter: %w", err)
	}

	p.ldapOpDuration, err = meter.Float64Histogram(
		"authentik_ldap_operation_duration_seconds",
		metric.WithDescription("Duration of LDAP operations"),
		metric.WithUnit("s"),
	)
	if err != nil {
		return fmt.Errorf("failed to create LDAP operation duration histogram: %w", err)
	}

	return nil
}

// GetTracer returns a tracer for the given name
func (p *Provider) GetTracer(name string) trace.Tracer {
	if !p.initialized {
		return trace.NewNoopTracerProvider().Tracer(name)
	}
	return otel.Tracer(name)
}

// GetMeter returns a meter for the given name
func (p *Provider) GetMeter(name string) metric.Meter {
	if !p.initialized {
		return noop.NewMeterProvider().Meter(name)
	}
	return otel.Meter(name)
}

// RecordRequest records HTTP request metrics
func (p *Provider) RecordRequest(ctx context.Context, method, status string, duration float64) {
	if !p.initialized || p.requestCounter == nil {
		return
	}

	attrs := metric.WithAttributes(
		attribute.String("method", method),
		attribute.String("status", status),
	)

	p.requestCounter.Add(ctx, 1, attrs)
	if p.requestDuration != nil {
		p.requestDuration.Record(ctx, duration, attrs)
	}
}

// RecordAuth records authentication metrics
func (p *Provider) RecordAuth(ctx context.Context, method string, success bool) {
	if !p.initialized || p.authCounter == nil {
		return
	}

	attrs := metric.WithAttributes(
		attribute.String("method", method),
		attribute.Bool("success", success),
	)

	p.authCounter.Add(ctx, 1, attrs)
}

// RecordLDAPOperation records LDAP operation metrics
func (p *Provider) RecordLDAPOperation(ctx context.Context, operation string, duration float64, success bool) {
	if !p.initialized || p.ldapOpCounter == nil {
		return
	}

	attrs := metric.WithAttributes(
		attribute.String("operation", operation),
		attribute.Bool("success", success),
	)

	p.ldapOpCounter.Add(ctx, 1, attrs)
	if p.ldapOpDuration != nil {
		p.ldapOpDuration.Record(ctx, duration, attrs)
	}
}

// Shutdown gracefully shuts down the telemetry provider
func (p *Provider) Shutdown(ctx context.Context) error {
	if !p.initialized {
		return nil
	}

	var err error
	if p.tracerProvider != nil {
		if shutdownErr := p.tracerProvider.Shutdown(ctx); shutdownErr != nil {
			err = fmt.Errorf("failed to shutdown tracer provider: %w", shutdownErr)
		}
	}

	if p.meterProvider != nil {
		if shutdownErr := p.meterProvider.Shutdown(ctx); shutdownErr != nil {
			if err != nil {
				err = fmt.Errorf("%w; failed to shutdown meter provider: %w", err, shutdownErr)
			} else {
				err = fmt.Errorf("failed to shutdown meter provider: %w", shutdownErr)
			}
		}
	}

	p.initialized = false
	return err
}

// getServiceName returns the configured service name or a default
func (p *Provider) getServiceName(serviceName string) string {
	if p.config.Telemetry.OTLP.ServiceName != "" {
		return p.config.Telemetry.OTLP.ServiceName
	}
	if serviceName != "" {
		return serviceName
	}
	return "authentik.outpost"
}

// getServiceVersion returns the configured service version or a default
func (p *Provider) getServiceVersion() string {
	if p.config.Telemetry.OTLP.ServiceVersion != "" {
		return p.config.Telemetry.OTLP.ServiceVersion
	}
	return "unknown"
}
