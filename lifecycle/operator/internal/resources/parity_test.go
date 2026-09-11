package resources_test

import (
	"os/exec"
	"path/filepath"
	"slices"
	"strings"
	"testing"

	"sigs.k8s.io/yaml"
)

// The builders in this package are a port of the Helm chart, so the chart is
// the reference for whether they are right. These tests render the real chart
// and compare, which catches a drifted object name or a missing field in a way
// hand-written expectations cannot.
//
// They skip when helm is not installed, so `make test` still works without it.

const chartPath = "../../../charts/authentik"

// renderChart runs `helm template` and returns the objects keyed by
// "<kind>/<name>".
func renderChart(t *testing.T, release string, values ...string) map[string]map[string]any {
	t.Helper()

	helm, err := exec.LookPath("helm")
	if err != nil {
		t.Skip("helm is not installed, skipping the chart parity comparison")
	}

	absChart, err := filepath.Abs(chartPath)
	if err != nil {
		t.Fatalf("failed to resolve the chart path: %v", err)
	}

	args := make([]string, 0, 5+2*len(values))
	args = append(args, "template", release, absChart, "--namespace", namespace)
	for _, value := range values {
		args = append(args, "--set", value)
	}

	output, err := exec.Command(helm, args...).CombinedOutput()
	if err != nil {
		// The chart's dependencies have to be vendored for this to work.
		if strings.Contains(string(output), "found in Chart.yaml, but missing in charts/") {
			t.Skipf("the chart's dependencies are not vendored, run: helm dependency update %s", chartPath)
		}
		t.Fatalf("helm template failed: %v\n%s", err, output)
	}

	return parseObjects(t, string(output))
}

func parseObjects(t *testing.T, manifest string) map[string]map[string]any {
	t.Helper()

	objects := map[string]map[string]any{}
	for doc := range strings.SplitSeq(manifest, "\n---") {
		if strings.TrimSpace(doc) == "" {
			continue
		}
		object := map[string]any{}
		if err := yaml.Unmarshal([]byte(doc), &object); err != nil {
			t.Fatalf("failed to parse a rendered document: %v\n%s", err, doc)
		}
		kind, _ := object["kind"].(string)
		if kind == "" {
			continue
		}
		metadata, _ := object["metadata"].(map[string]any)
		name, _ := metadata["name"].(string)
		objects[kind+"/"+name] = object
	}
	return objects
}

func keysOf(objects map[string]map[string]any) []string {
	keys := make([]string, 0, len(objects))
	for key := range objects {
		keys = append(keys, key)
	}
	slices.Sort(keys)
	return keys
}

func TestParityObjectNamesMatchTheChart(t *testing.T) {
	// Names and kinds have to match exactly, or an operator pointed at an
	// existing chart install would create a second copy of everything instead
	// of adopting what is there.
	chart := renderChart(t, name,
		"authentik.secret_key=x",
		"server.metrics.enabled=true",
		"worker.metrics.enabled=true",
		"server.ingress.enabled=true",
		"server.ingress.hosts[0]=authentik.example.com",
		"server.pdb.enabled=true",
		"worker.pdb.enabled=true",
		"prometheus.rules.enabled=true",
	)

	ours := buildOurs(t)

	// The chart renders these through subcharts the operator replaces with its
	// own implementation, so only the authentik-owned objects are comparable.
	skip := func(key string) bool {
		return strings.Contains(key, "postgresql") || strings.Contains(key, "redis")
	}

	missing := []string{}
	for _, key := range keysOf(chart) {
		if skip(key) {
			continue
		}
		if _, ok := ours[key]; !ok {
			missing = append(missing, key)
		}
	}
	if len(missing) > 0 {
		t.Errorf("the chart renders objects the operator does not build: %v\noperator builds: %v",
			missing, keysOf(ours))
	}

	extra := []string{}
	for _, key := range keysOf(ours) {
		if skip(key) {
			continue
		}
		if _, ok := chart[key]; !ok {
			extra = append(extra, key)
		}
	}
	if len(extra) > 0 {
		t.Errorf("the operator builds objects the chart does not render: %v", extra)
	}
}

func TestParitySelectorLabelsMatchTheChart(t *testing.T) {
	// A Deployment's selector is immutable. If these differ, adopting an
	// existing install is impossible: the apply would be rejected outright.
	chart := renderChart(t, name,
		"authentik.secret_key=x",
		"server.metrics.enabled=true",
		"worker.metrics.enabled=true",
		"server.ingress.enabled=true",
		"server.ingress.hosts[0]=authentik.example.com",
		"server.pdb.enabled=true",
		"worker.pdb.enabled=true",
		"prometheus.rules.enabled=true",
	)
	ours := buildOurs(t)

	for _, key := range []string{"Deployment/authentik-server", "Deployment/authentik-worker"} {
		chartObject, ok := chart[key]
		if !ok {
			t.Fatalf("%s missing from the chart output", key)
		}
		ourObject, ok := ours[key]
		if !ok {
			t.Fatalf("%s missing from the operator output", key)
		}

		chartSelector := dig(t, chartObject, "spec", "selector", "matchLabels")
		ourSelector := dig(t, ourObject, "spec", "selector", "matchLabels")
		if !equalMaps(chartSelector, ourSelector) {
			t.Errorf("%s selector differs:\n chart: %v\n  ours: %v", key, chartSelector, ourSelector)
		}
	}
}

func TestParityConfigSecretKeysMatchTheChart(t *testing.T) {
	// The flattening from nested config to AUTHENTIK_ env vars is the fiddliest
	// part of the port, so the key sets are compared directly.
	chart := renderChart(t, name,
		"authentik.secret_key=x",
		"authentik.email.host=smtp.example.com",
		"authentik.postgresql.password=p",
		"server.metrics.enabled=true",
		"worker.metrics.enabled=true",
		"server.ingress.enabled=true",
		"server.ingress.hosts[0]=authentik.example.com",
		"server.pdb.enabled=true",
		"worker.pdb.enabled=true",
		"prometheus.rules.enabled=true",
	)
	ours := buildOurs(t)

	chartData, _ := dig(t, chart["Secret/authentik"], "data").(map[string]any)
	ourData, _ := dig(t, ours["Secret/authentik"], "data").(map[string]any)

	chartKeys, ourKeys := sortedKeys(chartData), sortedKeys(ourData)

	// AUTHENTIK_ENABLED is the chart leaking its own `authentik.enabled` switch
	// into the Secret. authentik has no such option, so the operator does not
	// emit it and the comparison ignores it.
	chartKeys = without(chartKeys, "AUTHENTIK_ENABLED")

	if strings.Join(chartKeys, ",") != strings.Join(ourKeys, ",") {
		t.Errorf("configuration Secret keys differ:\n chart: %v\n  ours: %v", chartKeys, ourKeys)
	}
}

func without(values []string, drop string) []string {
	out := make([]string, 0, len(values))
	for _, value := range values {
		if value != drop {
			out = append(out, value)
		}
	}
	return out
}

func sortedKeys(m map[string]any) []string {
	keys := make([]string, 0, len(m))
	for key := range m {
		keys = append(keys, key)
	}
	slices.Sort(keys)
	return keys
}

func equalMaps(a, b any) bool {
	left, lok := a.(map[string]any)
	right, rok := b.(map[string]any)
	if !lok || !rok || len(left) != len(right) {
		return false
	}
	for key, value := range left {
		if right[key] != value {
			return false
		}
	}
	return true
}
