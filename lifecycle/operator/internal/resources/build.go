package resources

import (
	"encoding/json"
	"fmt"
	"reflect"

	apiextensionsv1 "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

// Build assembles every object that makes up the installation.
//
// The order is the order they are applied in, and it matters on a first
// install: the configuration Secret and the database have to exist before the
// Deployments that read them, or the pods crash-loop until the next reconcile.
func (b *Builder) Build() ([]client.Object, error) {
	objects := []client.Object{}

	add := func(object client.Object) {
		// Every builder returns a typed nil for "not wanted", which a plain nil
		// check on the interface would miss.
		if isNil(object) {
			return
		}
		objects = append(objects, object)
	}

	secret, err := b.ConfigSecret()
	if err != nil {
		return nil, err
	}
	add(secret)

	add(b.ServiceAccount())
	add(b.ServiceAccountTokenSecret())
	add(b.Role())
	add(b.RoleBinding())
	add(b.ClusterRole())
	add(b.ClusterRoleBinding())

	add(b.PostgreSQLSecret())
	add(b.PostgreSQLService())
	postgres, err := b.PostgreSQLStatefulSet()
	if err != nil {
		return nil, err
	}
	add(postgres)

	for _, c := range []*component{b.ServerComponent(), b.WorkerComponent()} {
		if c == nil {
			continue
		}

		deployment, err := b.Deployment(c)
		if err != nil {
			return nil, fmt.Errorf("failed to build the %s Deployment: %w", c.name, err)
		}
		add(deployment)

		add(b.MetricsService(c))
		add(b.HorizontalPodAutoscaler(c))
		add(b.PodDisruptionBudget(c))

		monitor, err := b.ServiceMonitor(c)
		if err != nil {
			return nil, fmt.Errorf("failed to build the %s ServiceMonitor: %w", c.name, err)
		}
		add(monitor)
	}

	if server := b.ServerComponent(); server != nil {
		add(b.ServerService(server))
		add(b.Ingress(server))

		route, err := b.Route(server)
		if err != nil {
			return nil, err
		}
		add(route)
	}

	rule, err := b.PrometheusRule()
	if err != nil {
		return nil, err
	}
	add(rule)

	return objects, nil
}

func decodeJSONList(items []apiextensionsv1.JSON, field string) ([]any, error) {
	if len(items) == 0 {
		return nil, nil
	}

	out := make([]any, 0, len(items))
	for i, item := range items {
		value, err := decodeJSON(item.Raw)
		if err != nil {
			return nil, fmt.Errorf("failed to decode %s[%d]: %w", field, i, err)
		}
		out = append(out, value)
	}
	return out, nil
}

// setJSONList decodes a freeform list into a key, leaving the key absent when
// the list is empty.
func setJSONList(target map[string]any, key string, items []apiextensionsv1.JSON, field string) error {
	decoded, err := decodeJSONList(items, field)
	if err != nil {
		return err
	}
	if len(decoded) > 0 {
		target[key] = decoded
	}
	return nil
}

func decodeJSON(raw []byte) (any, error) {
	var value any
	if err := json.Unmarshal(raw, &value); err != nil {
		return nil, err
	}
	return value, nil
}

// isNil reports whether the interface holds a nil pointer. A builder returning
// (*corev1.Service)(nil) for "not wanted" produces an interface that is itself
// non-nil, so a plain `object == nil` would let it through and the apply would
// panic.
func isNil(object client.Object) bool {
	if object == nil {
		return true
	}
	value := reflect.ValueOf(object)
	return value.Kind() == reflect.Pointer && value.IsNil()
}
