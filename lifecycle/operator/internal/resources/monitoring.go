package resources

import (
	"cmp"
	"embed"
	"fmt"
	"maps"
	"sync"

	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"sigs.k8s.io/yaml"

	akv1alpha1 "goauthentik.io/lifecycle/operator/api/v1alpha1"
)

// monitoringAPIVersion is the Prometheus Operator's API group.
//
// Both objects here are built unstructured rather than with the Prometheus
// Operator's Go types, because those CRDs are optional in a cluster and taking
// the dependency would tie this operator to their release cycle for a feature
// many installs never enable.
const monitoringAPIVersion = "monitoring.coreos.com/v1"

//go:embed assets/prometheusrule-groups.yaml
var promRuleAssets embed.FS

// prometheusRuleGroups are the recording rules and alerts the chart ships.
// Embedded as YAML rather than transcribed into Go: they are 41 static rules
// with no templating, so lifting the file verbatim keeps the two from
// drifting.
var prometheusRuleGroups = sync.OnceValues(func() ([]any, error) {
	raw, err := promRuleAssets.ReadFile("assets/prometheusrule-groups.yaml")
	if err != nil {
		return nil, fmt.Errorf("failed to read the embedded alerting rules: %w", err)
	}

	var groups []any
	if err := yaml.Unmarshal(raw, &groups); err != nil {
		return nil, fmt.Errorf("failed to parse the embedded alerting rules: %w", err)
	}
	return groups, nil
})

// ServiceMonitor tells the Prometheus Operator to scrape a component, or nil
// when it is not wanted.
func (b *Builder) ServiceMonitor(c *component) (*unstructured.Unstructured, error) {
	metrics := c.spec.Metrics
	if metrics == nil || !metrics.Enabled || metrics.ServiceMonitor == nil || !metrics.ServiceMonitor.Enabled {
		return nil, nil
	}
	spec := metrics.ServiceMonitor

	portName := defaultMetricsPortName
	if metrics.Service != nil && metrics.Service.PortName != "" {
		portName = metrics.Service.PortName
	}

	endpoint := map[string]any{
		"port":          portName,
		"path":          metricsPath,
		"interval":      cmp.Or(spec.Interval, defaultScrapeInterval),
		"scrapeTimeout": cmp.Or(spec.ScrapeTimeout, defaultScrapeTimeout),
	}
	if spec.Scheme != "" {
		endpoint["scheme"] = spec.Scheme
	}
	if err := setJSONList(endpoint, "relabelings", spec.Relabelings, "relabelings"); err != nil {
		return nil, err
	}
	if err := setJSONList(endpoint, "metricRelabelings", spec.MetricRelabelings, "metricRelabelings"); err != nil {
		return nil, err
	}
	if spec.TLSConfig != nil {
		tlsConfig, err := decodeJSON(spec.TLSConfig.Raw)
		if err != nil {
			return nil, fmt.Errorf("failed to decode tlsConfig: %w", err)
		}
		endpoint["tlsConfig"] = tlsConfig
	}

	// The metrics component label distinguishes this from the component's main
	// Service, which shares the same selector labels otherwise.
	metricsComponent := c.name + "-metrics"

	monitor := &unstructured.Unstructured{Object: map[string]any{
		"apiVersion": monitoringAPIVersion,
		"kind":       "ServiceMonitor",
		"spec": map[string]any{
			"endpoints": []any{endpoint},
			"namespaceSelector": map[string]any{
				"matchNames": []any{b.Namespace()},
			},
			"selector": map[string]any{
				"matchLabels": toAnyMap(b.SelectorLabels(metricsComponent)),
			},
		},
	}}
	monitor.SetName(c.objectName)
	// A ServiceMonitor may live in the namespace Prometheus watches rather than
	// alongside authentik.
	monitor.SetNamespace(cmp.Or(spec.Namespace, b.Namespace()))
	monitor.SetLabels(mergedMap(b.Labels(metricsComponent), spec.Selector, spec.Labels))
	monitor.SetAnnotations(spec.Annotations)

	return monitor, nil
}

// PrometheusRule ships authentik's recording rules and alerts, or nil when not
// wanted.
func (b *Builder) PrometheusRule() (*unstructured.Unstructured, error) {
	prometheus := b.Authentik.Spec.Prometheus
	if prometheus == nil || prometheus.Rules == nil || !prometheus.Rules.Enabled {
		return nil, nil
	}
	spec := prometheus.Rules

	groups, err := prometheusRuleGroups()
	if err != nil {
		return nil, err
	}
	groups = withGroupAnnotations(groups, spec)

	rule := &unstructured.Unstructured{Object: map[string]any{
		"apiVersion": monitoringAPIVersion,
		"kind":       "PrometheusRule",
		"spec":       map[string]any{"groups": groups},
	}}
	rule.SetName(b.Authentik.Fullname())
	rule.SetNamespace(cmp.Or(spec.Namespace, b.Namespace()))
	rule.SetLabels(mergedMap(b.Labels(""), spec.Selector, spec.Labels))
	rule.SetAnnotations(spec.Annotations)

	return rule, nil
}

// withGroupAnnotations copies the rule groups, adding the user's annotations to
// each. The embedded groups are shared, so they must not be mutated.
func withGroupAnnotations(groups []any, spec *akv1alpha1.PrometheusRulesSpec) []any {
	out := make([]any, 0, len(groups))
	for _, raw := range groups {
		group, ok := raw.(map[string]any)
		if !ok {
			out = append(out, raw)
			continue
		}

		copied := make(map[string]any, len(group)+1)
		maps.Copy(copied, group)
		if len(spec.AdditionalRuleGroupAnnotations) > 0 {
			copied["annotations"] = toAnyMap(spec.AdditionalRuleGroupAnnotations)
		}
		out = append(out, copied)
	}
	return out
}

func toAnyMap(in map[string]string) map[string]any {
	out := make(map[string]any, len(in))
	for key, value := range in {
		out[key] = value
	}
	return out
}
