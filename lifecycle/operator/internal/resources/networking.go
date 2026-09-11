package resources

import (
	"cmp"
	"fmt"
	"slices"

	networkingv1 "k8s.io/api/networking/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/utils/ptr"
)

// Ingress routes external traffic to the server, or nil when disabled.
func (b *Builder) Ingress(c *component) *networkingv1.Ingress {
	server := b.Authentik.Spec.Server
	if server == nil || server.Ingress == nil || !server.Ingress.Enabled {
		return nil
	}
	spec := server.Ingress

	port := b.servicePort(spec.HTTPS)
	pathType := networkingv1.PathType(cmp.Or(spec.PathType, defaultPathType))

	paths := spec.Paths
	if len(paths) == 0 {
		// The chart defaults this to the path authentik is served under.
		paths = []string{b.webPath()}
	}

	rulePaths := slices.Clone(spec.ExtraPaths)
	for _, path := range paths {
		rulePaths = append(rulePaths, networkingv1.HTTPIngressPath{
			Path:     path,
			PathType: &pathType,
			Backend: networkingv1.IngressBackend{
				Service: &networkingv1.IngressServiceBackend{
					Name: b.ServerName(),
					Port: networkingv1.ServiceBackendPort{Number: port},
				},
			},
		})
	}

	rule := networkingv1.IngressRule{
		IngressRuleValue: networkingv1.IngressRuleValue{
			HTTP: &networkingv1.HTTPIngressRuleValue{Paths: rulePaths},
		},
	}

	// With no hosts, a single host-less rule matches every hostname.
	rules := []networkingv1.IngressRule{}
	if len(spec.Hosts) == 0 {
		rules = append(rules, rule)
	}
	for _, host := range spec.Hosts {
		hostRule := rule
		hostRule.Host = host
		rules = append(rules, hostRule)
	}

	ingress := &networkingv1.Ingress{
		ObjectMeta: b.objectMeta(b.ServerName(), c.name, spec.Labels, spec.Annotations),
		Spec: networkingv1.IngressSpec{
			Rules: rules,
			TLS:   spec.TLS,
		},
	}
	if spec.IngressClassName != "" {
		ingress.Spec.IngressClassName = ptr.To(spec.IngressClassName)
	}

	return ingress
}

// Route builds the Gateway API route in front of the server, or nil when
// disabled.
//
// Built unstructured because the Gateway API types are not a dependency of this
// operator: its CRDs are optional in a cluster, and taking the dependency would
// mean tracking their release cycle for a feature many installs never turn on.
func (b *Builder) Route(c *component) (*unstructured.Unstructured, error) {
	server := b.Authentik.Spec.Server
	if server == nil || server.Route == nil || server.Route.Main == nil || !server.Route.Main.Enabled {
		return nil, nil
	}
	spec := server.Route.Main

	rules := []any{}
	for i, raw := range spec.AdditionalRules {
		rule, err := decodeJSON(raw.Raw)
		if err != nil {
			return nil, fmt.Errorf("failed to decode server.route.main.additionalRules[%d]: %w", i, err)
		}
		rules = append(rules, rule)
	}

	if spec.HTTPSRedirect != nil && *spec.HTTPSRedirect {
		rules = append(rules, map[string]any{
			"filters": []any{map[string]any{
				"type": "RequestRedirect",
				"requestRedirect": map[string]any{
					"scheme":     "https",
					"statusCode": int64(301),
				},
			}},
		})
	} else {
		rule := map[string]any{
			"backendRefs": []any{map[string]any{
				"group":  "",
				"kind":   "Service",
				"name":   b.ServerName(),
				"port":   int64(b.servicePort(spec.HTTPS)),
				"weight": int64(1),
			}},
		}
		filters, err := decodeJSONList(spec.Filters, "server.route.main.filters")
		if err != nil {
			return nil, err
		}
		if len(filters) > 0 {
			rule["filters"] = filters
		}

		matches, err := decodeJSONList(spec.Matches, "server.route.main.matches")
		if err != nil {
			return nil, err
		}
		if len(matches) == 0 {
			// The chart defaults to matching everything under authentik's path.
			matches = []any{map[string]any{
				"path": map[string]any{"type": "PathPrefix", "value": b.webPath()},
			}}
		}
		rule["matches"] = matches

		rules = append(rules, rule)
	}

	routeSpec := map[string]any{"rules": rules}

	parentRefs, err := decodeJSONList(spec.ParentRefs, "server.route.main.parentRefs")
	if err != nil {
		return nil, err
	}
	if len(parentRefs) > 0 {
		routeSpec["parentRefs"] = parentRefs
	}
	if len(spec.Hostnames) > 0 {
		hostnames := make([]any, 0, len(spec.Hostnames))
		for _, hostname := range spec.Hostnames {
			hostnames = append(hostnames, hostname)
		}
		routeSpec["hostnames"] = hostnames
	}

	route := &unstructured.Unstructured{Object: map[string]any{
		"apiVersion": cmp.Or(spec.APIVersion, "gateway.networking.k8s.io/v1"),
		"kind":       cmp.Or(spec.Kind, "HTTPRoute"),
		"spec":       routeSpec,
	}}
	route.SetName(b.ServerName())
	route.SetNamespace(b.Namespace())
	route.SetLabels(mergedMap(b.Labels(c.name), spec.Labels))
	route.SetAnnotations(spec.Annotations)

	return route, nil
}

// servicePort picks the server Service port that traffic should reach, honoring
// the https switch shared by the Ingress and the route.
func (b *Builder) servicePort(https *bool) int32 {
	spec := b.Authentik.Spec.Server
	if https != nil && *https {
		if spec != nil && spec.Service != nil {
			return ptr.Deref(spec.Service.ServicePortHTTPS, defaultServicePortHTTPS)
		}
		return defaultServicePortHTTPS
	}
	if spec != nil && spec.Service != nil {
		return ptr.Deref(spec.Service.ServicePortHTTP, defaultServicePortHTTP)
	}
	return defaultServicePortHTTP
}
