package resources_test

import (
	"encoding/base64"
	"reflect"
	"strings"
	"testing"

	corev1 "k8s.io/api/core/v1"
	apiextensionsv1 "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/util/intstr"
	"sigs.k8s.io/yaml"

	akv1alpha1 "goauthentik.io/lifecycle/operator/api/v1alpha1"
	"goauthentik.io/lifecycle/operator/internal/resources"
)

func ptr[T any](v T) *T { return &v }

func ptrIntOrString(value string) *intstr.IntOrString {
	parsed := intstr.FromString(value)
	return &parsed
}

// decodeSecretValue reads a Secret data value, which the unstructured
// converter leaves base64-encoded.
func decodeSecretValue(t *testing.T, raw any) string {
	t.Helper()

	encoded, ok := raw.(string)
	if !ok {
		t.Fatalf("expected a string, got %T", raw)
	}
	decoded, err := base64.StdEncoding.DecodeString(encoded)
	if err != nil {
		// Already plain, which happens for values the converter leaves alone.
		return encoded
	}
	return string(decoded)
}

const (
	name      = "authentik"
	namespace = "authentik"
	testTag   = "2026.8.0"
	testSMTP  = "smtp.example.com"
	testLevel = "debug"
)

// build renders the objects for a spec, keyed by "<kind>/<name>".
func build(t *testing.T, spec akv1alpha1.AuthentikSpec) map[string]map[string]any {
	t.Helper()

	ak := &akv1alpha1.Authentik{
		ObjectMeta: metav1.ObjectMeta{Name: name, Namespace: namespace},
		Spec:       spec,
	}
	builder := &resources.Builder{Authentik: ak, Version: testTag}

	objects, err := builder.Build()
	if err != nil {
		t.Fatalf("Build: %v", err)
	}

	out := map[string]map[string]any{}
	for _, object := range objects {
		content, err := runtime.DefaultUnstructuredConverter.ToUnstructured(object)
		if err != nil {
			t.Fatalf("failed to convert %T: %v", object, err)
		}

		kind := object.GetObjectKind().GroupVersionKind().Kind
		if kind == "" {
			// Typed objects carry no kind until they pass through a scheme;
			// the Go type name is enough to key a test by.
			kind = reflect.TypeOf(object).Elem().Name()
		}
		out[kind+"/"+object.GetName()] = content
	}
	return out
}

// buildOurs renders the same configuration the parity tests render the chart
// with, so the two can be compared object for object. Any --set the parity
// tests pass to helm has to have its equivalent here.
func buildOurs(t *testing.T) map[string]map[string]any {
	t.Helper()

	metrics := func() *akv1alpha1.MetricsSpec {
		return &akv1alpha1.MetricsSpec{Enabled: true}
	}

	return build(t, akv1alpha1.AuthentikSpec{
		Global: &akv1alpha1.GlobalSpec{
			Image: &akv1alpha1.ImageSpec{Tag: testTag},
		},
		Authentik: &akv1alpha1.AuthentikConfigSpec{
			SecretKey: "x",
			Email:     &akv1alpha1.AuthentikEmailConfig{Host: testSMTP},
			PostgreSQL: &akv1alpha1.AuthentikPostgreSQLConfig{
				Password: "p",
			},
		},
		Server: &akv1alpha1.ServerSpec{
			ComponentSpec: akv1alpha1.ComponentSpec{
				Metrics: metrics(),
				PDB:     &akv1alpha1.PDBSpec{Enabled: true},
			},
			Ingress: &akv1alpha1.IngressSpec{
				Enabled: true,
				Hosts:   []string{"authentik.example.com"},
			},
		},
		Worker: &akv1alpha1.WorkerSpec{
			ComponentSpec: akv1alpha1.ComponentSpec{
				Metrics: metrics(),
				PDB:     &akv1alpha1.PDBSpec{Enabled: true},
			},
		},
		Prometheus: &akv1alpha1.PrometheusSpec{
			Rules: &akv1alpha1.PrometheusRulesSpec{Enabled: true},
		},
	})
}

func dig(t *testing.T, object map[string]any, path ...string) any {
	t.Helper()

	var current any = object
	for i, key := range path {
		asMap, ok := current.(map[string]any)
		if !ok {
			t.Fatalf("%s is not an object", strings.Join(path[:i], "."))
		}
		current, ok = asMap[key]
		if !ok {
			t.Fatalf("%s is not set", strings.Join(path[:i+1], "."))
		}
	}
	return current
}

func mustGet(t *testing.T, objects map[string]map[string]any, key string) map[string]any {
	t.Helper()

	object, ok := objects[key]
	if !ok {
		t.Fatalf("%s was not built, got: %v", key, keysOf(objects))
	}
	return object
}

func firstContainer(t *testing.T, object map[string]any) map[string]any {
	t.Helper()

	containers, ok := dig(t, object, "spec", "template", "spec", "containers").([]any)
	if !ok || len(containers) == 0 {
		t.Fatal("the object has no containers")
	}
	container, ok := containers[0].(map[string]any)
	if !ok {
		t.Fatal("the first container is not an object")
	}
	return container
}

func minimalSpec() akv1alpha1.AuthentikSpec {
	return akv1alpha1.AuthentikSpec{
		Global:    &akv1alpha1.GlobalSpec{Image: &akv1alpha1.ImageSpec{Tag: testTag}},
		Authentik: &akv1alpha1.AuthentikConfigSpec{SecretKey: "x"},
	}
}

func TestBuildDefaults(t *testing.T) {
	objects := build(t, minimalSpec())

	for _, key := range []string{
		"Deployment/authentik-server",
		"Deployment/authentik-worker",
		"Service/authentik-server",
		"Secret/authentik",
		"ServiceAccount/authentik",
		"Role/authentik",
		"RoleBinding/authentik",
		"ClusterRole/authentik-authentik",
		"ClusterRoleBinding/authentik-authentik",
	} {
		mustGet(t, objects, key)
	}

	// Off unless asked for, matching the chart.
	for _, key := range []string{
		"Ingress/authentik-server",
		"HorizontalPodAutoscaler/authentik-server",
		"PodDisruptionBudget/authentik-server",
		"StatefulSet/authentik-postgresql",
		"PrometheusRule/authentik",
	} {
		if _, ok := objects[key]; ok {
			t.Errorf("%s should not be built by default", key)
		}
	}

	server := mustGet(t, objects, "Deployment/authentik-server")
	if got := firstContainer(t, server)["image"]; got != "ghcr.io/goauthentik/server:"+testTag {
		t.Errorf("server image = %v", got)
	}
	args, _ := firstContainer(t, server)["args"].([]any)
	if len(args) != 1 || args[0] != "server" {
		t.Errorf("server args = %v, want [server]", args)
	}

	worker := mustGet(t, objects, "Deployment/authentik-worker")
	args, _ = firstContainer(t, worker)["args"].([]any)
	if len(args) != 1 || args[0] != "worker" {
		t.Errorf("worker args = %v, want [worker]", args)
	}
	// Only the worker talks to the Kubernetes API, so only it gets the outpost
	// ServiceAccount.
	if got := dig(t, worker, "spec", "template", "spec", "serviceAccountName"); got != name {
		t.Errorf("worker serviceAccountName = %v, want %s", got, name)
	}
	if _, ok := dig(t, server, "spec", "template", "spec").(map[string]any)["serviceAccountName"]; ok {
		t.Error("the server should not get a ServiceAccount by default")
	}
}

func TestBuildConfigSecretFlattening(t *testing.T) {
	objects := build(t, akv1alpha1.AuthentikSpec{
		Global: &akv1alpha1.GlobalSpec{Image: &akv1alpha1.ImageSpec{Tag: testTag}},
		Authentik: &akv1alpha1.AuthentikConfigSpec{
			LogLevel:  testLevel,
			SecretKey: "x",
			Email: &akv1alpha1.AuthentikEmailConfig{
				Host:   testSMTP,
				Port:   ptr(int32(465)),
				UseSSL: ptr(true),
			},
			ExtraConfig: &apiextensionsv1.JSON{
				Raw: []byte(`{"cache":{"timeout":600},"footer_links":[{"name":"Docs"}]}`),
			},
		},
	})

	data, _ := dig(t, mustGet(t, objects, "Secret/authentik"), "data").(map[string]any)

	// Nested keys join with a double underscore, and the whole thing is
	// upper-cased and AUTHENTIK_-prefixed.
	for key, want := range map[string]string{
		"AUTHENTIK_LOG_LEVEL":      testLevel,
		"AUTHENTIK_SECRET_KEY":     "x",
		"AUTHENTIK_EMAIL__HOST":    testSMTP,
		"AUTHENTIK_EMAIL__PORT":    "465",
		"AUTHENTIK_EMAIL__USE_SSL": "true",
		"AUTHENTIK_CACHE__TIMEOUT": "600",
	} {
		raw, ok := data[key]
		if !ok {
			t.Errorf("%s is missing, got %v", key, sortedKeys(data))
			continue
		}
		if got := decodeSecretValue(t, raw); got != want {
			t.Errorf("%s = %q, want %q", key, got, want)
		}
	}

	// A list-valued option has to reach authentik as JSON, not as Go's
	// fmt rendering of a slice.
	if got := decodeSecretValue(t, data["AUTHENTIK_FOOTER_LINKS"]); got != `[{"name":"Docs"}]` {
		t.Errorf("AUTHENTIK_FOOTER_LINKS = %q", got)
	}

	// An unset option must be absent rather than empty, because authentik
	// distinguishes the two.
	if _, ok := data["AUTHENTIK_EMAIL__USERNAME"]; ok {
		t.Error("an empty option should be omitted, not set to an empty string")
	}
	if _, ok := data["AUTHENTIK_EXTRACONFIG"]; ok {
		t.Error("extraConfig is the operator's own field and must not become an env var")
	}
}

func TestBuildConfigChecksumChangesWithTheConfig(t *testing.T) {
	// Without this the pods would keep running against an old configuration
	// after a Secret change.
	first := build(t, minimalSpec())

	changed := minimalSpec()
	changed.Authentik.LogLevel = testLevel
	second := build(t, changed)

	annotationPath := []string{"spec", "template", "metadata", "annotations"}
	a := dig(t, mustGet(t, first, "Deployment/authentik-server"), annotationPath...).(map[string]any)
	b := dig(t, mustGet(t, second, "Deployment/authentik-server"), annotationPath...).(map[string]any)

	if a["checksum/secret"] == b["checksum/secret"] {
		t.Error("the config checksum did not change when the configuration did")
	}

	// It also has to be stable, or every reconcile would restart the pods.
	again := build(t, minimalSpec())
	c := dig(t, mustGet(t, again, "Deployment/authentik-server"), annotationPath...).(map[string]any)
	if a["checksum/secret"] != c["checksum/secret"] {
		t.Error("the config checksum is not stable across builds")
	}
}

func TestBuildDefaultProbes(t *testing.T) {
	objects := build(t, minimalSpec())

	server := firstContainer(t, mustGet(t, objects, "Deployment/authentik-server"))
	if got := dig(t, server, "livenessProbe", "httpGet", "path"); got != "/-/health/live/" {
		t.Errorf("server liveness path = %v, want /-/health/live/", got)
	}
	if got := dig(t, server, "readinessProbe", "httpGet", "path"); got != "/-/health/ready/" {
		t.Errorf("server readiness path = %v, want /-/health/ready/", got)
	}

	// The worker has no HTTP server to probe, so it runs the healthcheck
	// command instead.
	worker := firstContainer(t, mustGet(t, objects, "Deployment/authentik-worker"))
	command, _ := dig(t, worker, "livenessProbe", "exec", "command").([]any)
	if len(command) != 2 || command[0] != "ak" || command[1] != "healthcheck" {
		t.Errorf("worker liveness command = %v, want [ak healthcheck]", command)
	}
}

func TestBuildProbePathFollowsWebPath(t *testing.T) {
	spec := minimalSpec()
	spec.Authentik.Web = &akv1alpha1.AuthentikWebConfig{Path: "/authentik/"}

	server := firstContainer(t, mustGet(t, build(t, spec), "Deployment/authentik-server"))
	if got := dig(t, server, "livenessProbe", "httpGet", "path"); got != "/authentik/-/health/live/" {
		t.Errorf("liveness path = %v, want /authentik/-/health/live/", got)
	}
}

func TestBuildDefaultAffinitySpreadsReplicas(t *testing.T) {
	// The chart's default is a soft anti-affinity, which the CRD does not carry
	// as a default of its own.
	server := mustGet(t, build(t, minimalSpec()), "Deployment/authentik-server")
	preferred, ok := dig(t, server, "spec", "template", "spec", "affinity",
		"podAntiAffinity", "preferredDuringSchedulingIgnoredDuringExecution").([]any)
	if !ok || len(preferred) != 1 {
		t.Fatalf("expected one preferred anti-affinity term, got %v", preferred)
	}
	term := preferred[0].(map[string]any)
	if got := dig(t, term, "podAffinityTerm", "topologyKey"); got != "kubernetes.io/hostname" {
		t.Errorf("topologyKey = %v", got)
	}
}

func TestBuildAutoscalingLeavesReplicasUnset(t *testing.T) {
	spec := minimalSpec()
	spec.Server = &akv1alpha1.ServerSpec{
		ComponentSpec: akv1alpha1.ComponentSpec{
			Replicas: ptr(int32(3)),
			Autoscaling: &akv1alpha1.AutoscalingSpec{
				Enabled:                        true,
				MinReplicas:                    ptr(int32(2)),
				MaxReplicas:                    ptr(int32(8)),
				TargetCPUUtilizationPercentage: ptr(int32(70)),
			},
		},
	}
	objects := build(t, spec)

	// Setting both would have the Deployment and the autoscaler fight.
	server := mustGet(t, objects, "Deployment/authentik-server")
	if _, ok := dig(t, server, "spec").(map[string]any)["replicas"]; ok {
		t.Error("replicas is set while autoscaling is enabled")
	}

	hpa := mustGet(t, objects, "HorizontalPodAutoscaler/authentik-server")
	if got := dig(t, hpa, "spec", "maxReplicas"); got != int64(8) {
		t.Errorf("maxReplicas = %v, want 8", got)
	}
	if got := dig(t, hpa, "spec", "scaleTargetRef", "name"); got != "authentik-server" {
		t.Errorf("scaleTargetRef = %v", got)
	}
}

func TestBuildDisablingAComponent(t *testing.T) {
	spec := minimalSpec()
	spec.Worker = &akv1alpha1.WorkerSpec{
		ComponentSpec: akv1alpha1.ComponentSpec{Enabled: ptr(false)},
	}
	objects := build(t, spec)

	mustGet(t, objects, "Deployment/authentik-server")
	if _, ok := objects["Deployment/authentik-worker"]; ok {
		t.Error("the worker Deployment was built while worker.enabled is false")
	}
}

func TestBuildGeoIPSidecar(t *testing.T) {
	spec := minimalSpec()
	spec.GeoIP = &akv1alpha1.GeoIPSpec{
		Enabled:    true,
		AccountID:  "123456",
		LicenseKey: "k",
	}
	objects := build(t, spec)

	server := mustGet(t, objects, "Deployment/authentik-server")
	containers, _ := dig(t, server, "spec", "template", "spec", "containers").([]any)
	if len(containers) != 2 {
		t.Fatalf("expected 2 containers, got %d", len(containers))
	}
	if got := containers[1].(map[string]any)["name"]; got != "geoip" {
		t.Errorf("second container = %v, want geoip", got)
	}

	// The credentials ride in the same Secret as the rest of the config.
	data, _ := dig(t, mustGet(t, objects, "Secret/authentik"), "data").(map[string]any)
	for _, key := range []string{"GEOIPUPDATE_ACCOUNT_ID", "GEOIPUPDATE_LICENSE_KEY"} {
		if _, ok := data[key]; !ok {
			t.Errorf("%s is missing from the Secret", key)
		}
	}
}

func TestBuildGeoIPRequiresCredentials(t *testing.T) {
	ak := &akv1alpha1.Authentik{
		ObjectMeta: metav1.ObjectMeta{Name: name, Namespace: namespace},
		Spec:       minimalSpec(),
	}
	ak.Spec.GeoIP = &akv1alpha1.GeoIPSpec{Enabled: true}

	builder := &resources.Builder{Authentik: ak, Version: testTag}
	if _, err := builder.Build(); err == nil {
		t.Fatal("expected an error when GeoIP is enabled without credentials")
	}
}

func TestBuildBlueprintMountsOnlyOnTheWorker(t *testing.T) {
	spec := minimalSpec()
	spec.Blueprints = &akv1alpha1.BlueprintsSpec{ConfigMaps: []string{"custom"}}
	objects := build(t, spec)

	worker := firstContainer(t, mustGet(t, objects, "Deployment/authentik-worker"))
	mounts, _ := worker["volumeMounts"].([]any)
	found := false
	for _, raw := range mounts {
		if raw.(map[string]any)["mountPath"] == "/blueprints/mounted/cm-custom" {
			found = true
		}
	}
	if !found {
		t.Errorf("the blueprint ConfigMap is not mounted on the worker, got %v", mounts)
	}

	// The server does not apply blueprints, so mounting them there is noise.
	server := firstContainer(t, mustGet(t, objects, "Deployment/authentik-server"))
	if mounts, _ := server["volumeMounts"].([]any); len(mounts) != 0 {
		t.Errorf("the server should have no blueprint mounts, got %v", mounts)
	}
}

func TestBuildBundledPostgreSQL(t *testing.T) {
	spec := minimalSpec()
	spec.PostgreSQL = &akv1alpha1.PostgreSQLSpec{
		Enabled: ptr(true),
		Auth:    &akv1alpha1.PostgreSQLAuthSpec{Password: "p"},
		Primary: &akv1alpha1.PostgreSQLPrimarySpec{
			Persistence: &akv1alpha1.PostgreSQLPersistenceSpec{Size: "16Gi"},
		},
	}
	objects := build(t, spec)

	statefulSet := mustGet(t, objects, "StatefulSet/authentik-postgresql")
	claims, _ := dig(t, statefulSet, "spec", "volumeClaimTemplates").([]any)
	if len(claims) != 1 {
		t.Fatalf("expected one volume claim template, got %v", claims)
	}
	if got := dig(t, claims[0].(map[string]any), "spec", "resources", "requests", "storage"); got != "16Gi" {
		t.Errorf("storage = %v, want 16Gi", got)
	}

	mustGet(t, objects, "Service/authentik-postgresql")
	mustGet(t, objects, "Secret/authentik-postgresql")

	// authentik has to be pointed at the database the operator just created,
	// which the chart did with a templated default.
	data, _ := dig(t, mustGet(t, objects, "Secret/authentik"), "data").(map[string]any)
	if got := decodeSecretValue(t, data["AUTHENTIK_POSTGRESQL__HOST"]); got != "authentik-postgresql" {
		t.Errorf("AUTHENTIK_POSTGRESQL__HOST = %q, want authentik-postgresql", got)
	}
}

func TestBuildPostgreSQLRequiresAPassword(t *testing.T) {
	ak := &akv1alpha1.Authentik{
		ObjectMeta: metav1.ObjectMeta{Name: name, Namespace: namespace},
		Spec:       minimalSpec(),
	}
	ak.Spec.PostgreSQL = &akv1alpha1.PostgreSQLSpec{Enabled: ptr(true)}

	builder := &resources.Builder{Authentik: ak, Version: testTag}
	if _, err := builder.Build(); err == nil {
		t.Fatal("expected an error when the database is enabled without a password")
	}
}

func TestBuildPrometheusRuleCarriesTheChartsRules(t *testing.T) {
	spec := minimalSpec()
	spec.Prometheus = &akv1alpha1.PrometheusSpec{
		Rules: &akv1alpha1.PrometheusRulesSpec{Enabled: true},
	}

	rule := mustGet(t, build(t, spec), "PrometheusRule/authentik")
	groups, _ := dig(t, rule, "spec", "groups").([]any)
	if len(groups) != 6 {
		t.Fatalf("expected the chart's 6 rule groups, got %d", len(groups))
	}

	total := 0
	for _, raw := range groups {
		rules, _ := raw.(map[string]any)["rules"].([]any)
		total += len(rules)
	}
	if total != 41 {
		t.Errorf("expected the chart's 41 rules, got %d", total)
	}
}

func TestBuildOwnerLabelDistinguishesInstances(t *testing.T) {
	// Two instances in one namespace must not prune each other's objects.
	first := build(t, minimalSpec())

	other := &akv1alpha1.Authentik{
		ObjectMeta: metav1.ObjectMeta{Name: "other", Namespace: namespace},
		Spec:       minimalSpec(),
	}
	builder := &resources.Builder{Authentik: other, Version: testTag}
	objects, err := builder.Build()
	if err != nil {
		t.Fatalf("Build: %v", err)
	}

	firstLabels, _ := dig(t, mustGet(t, first, "Deployment/authentik-server"), "metadata", "labels").(map[string]any)
	var secondOwner string
	for _, object := range objects {
		if object.GetName() == "other-authentik-server" {
			secondOwner = object.GetLabels()[resources.InstanceOwnerLabel]
		}
	}

	if secondOwner == "" {
		t.Fatal("the second instance's Deployment was not built")
	}
	if firstLabels[resources.InstanceOwnerLabel] == secondOwner {
		t.Error("two instances share an owner label, so pruning would cross between them")
	}
}

func TestBuildMetricsAndServiceMonitor(t *testing.T) {
	spec := minimalSpec()
	spec.Server = &akv1alpha1.ServerSpec{
		ComponentSpec: akv1alpha1.ComponentSpec{
			Metrics: &akv1alpha1.MetricsSpec{
				Enabled:        true,
				ServiceMonitor: &akv1alpha1.ServiceMonitorSpec{Enabled: true},
			},
		},
	}
	objects := build(t, spec)

	mustGet(t, objects, "Service/authentik-server-metrics")
	monitor := mustGet(t, objects, "ServiceMonitor/authentik-server")

	if got := dig(t, monitor, "apiVersion"); got != "monitoring.coreos.com/v1" {
		t.Errorf("apiVersion = %v", got)
	}
	endpoints, _ := dig(t, monitor, "spec", "endpoints").([]any)
	if len(endpoints) != 1 {
		t.Fatalf("expected one endpoint, got %v", endpoints)
	}
	if got := endpoints[0].(map[string]any)["path"]; got != "/metrics" {
		t.Errorf("path = %v, want /metrics", got)
	}

	// The monitor must select the metrics Service, not the main one.
	selector, _ := dig(t, monitor, "spec", "selector", "matchLabels").(map[string]any)
	if selector["app.kubernetes.io/component"] != "server-metrics" {
		t.Errorf("selector = %v, want the server-metrics component", selector)
	}
}

func TestBuildIngress(t *testing.T) {
	spec := minimalSpec()
	spec.Server = &akv1alpha1.ServerSpec{
		Ingress: &akv1alpha1.IngressSpec{
			Enabled:          true,
			IngressClassName: "nginx",
			Hosts:            []string{"a.example.com", "b.example.com"},
		},
	}

	ingress := mustGet(t, build(t, spec), "Ingress/authentik-server")
	if got := dig(t, ingress, "spec", "ingressClassName"); got != "nginx" {
		t.Errorf("ingressClassName = %v", got)
	}

	rules, _ := dig(t, ingress, "spec", "rules").([]any)
	if len(rules) != 2 {
		t.Fatalf("expected a rule per host, got %d", len(rules))
	}
	// The default path is whatever authentik is served under.
	paths, _ := dig(t, rules[0].(map[string]any), "http", "paths").([]any)
	if got := paths[0].(map[string]any)["path"]; got != "/" {
		t.Errorf("path = %v, want /", got)
	}
	if got := dig(t, paths[0].(map[string]any), "backend", "service", "port", "number"); got != int64(80) {
		t.Errorf("backend port = %v, want 80", got)
	}
}

func TestBuildRecreateStrategyDropsRollingUpdate(t *testing.T) {
	// The API server rejects a rollingUpdate block alongside Recreate.
	spec := minimalSpec()
	spec.Global.DeploymentStrategy = &akv1alpha1.DeploymentStrategy{
		Type:          "RollingUpdate",
		RollingUpdate: &akv1alpha1.RollingUpdate{MaxSurge: ptrIntOrString("25%")},
	}
	spec.Server = &akv1alpha1.ServerSpec{
		ComponentSpec: akv1alpha1.ComponentSpec{
			DeploymentStrategy: &akv1alpha1.DeploymentStrategy{Type: "Recreate"},
		},
	}

	server := mustGet(t, build(t, spec), "Deployment/authentik-server")
	strategy, _ := dig(t, server, "spec", "strategy").(map[string]any)
	if strategy["type"] != "Recreate" {
		t.Errorf("type = %v, want Recreate", strategy["type"])
	}
	if _, ok := strategy["rollingUpdate"]; ok {
		t.Error("rollingUpdate must not be set alongside Recreate")
	}
}

func TestBuildSecurityContextMergesOverGlobal(t *testing.T) {
	// The chart deep-merges these, so a component overriding one field keeps
	// the global value of the others.
	spec := minimalSpec()
	spec.Global.SecurityContext = &corev1.PodSecurityContext{
		RunAsUser: ptr(int64(1000)),
		FSGroup:   ptr(int64(2000)),
	}
	spec.Server = &akv1alpha1.ServerSpec{
		ComponentSpec: akv1alpha1.ComponentSpec{
			SecurityContext: &corev1.PodSecurityContext{RunAsUser: ptr(int64(1001))},
		},
	}

	server := mustGet(t, build(t, spec), "Deployment/authentik-server")
	context, _ := dig(t, server, "spec", "template", "spec", "securityContext").(map[string]any)
	if context["runAsUser"] != int64(1001) {
		t.Errorf("runAsUser = %v, want the component override 1001", context["runAsUser"])
	}
	if context["fsGroup"] != int64(2000) {
		t.Errorf("fsGroup = %v, want the global value 2000 to survive", context["fsGroup"])
	}
}

func TestBuildYAMLIsValid(t *testing.T) {
	// Everything the operator builds has to survive a round trip through YAML,
	// which is what catches a field that cannot be serialized.
	objects := build(t, akv1alpha1.AuthentikSpec{
		Global:    &akv1alpha1.GlobalSpec{Image: &akv1alpha1.ImageSpec{Tag: testTag}},
		Authentik: &akv1alpha1.AuthentikConfigSpec{SecretKey: "x"},
		PostgreSQL: &akv1alpha1.PostgreSQLSpec{
			Enabled: ptr(true),
			Auth:    &akv1alpha1.PostgreSQLAuthSpec{Password: "p"},
		},
	})

	for key, object := range objects {
		encoded, err := yaml.Marshal(object)
		if err != nil {
			t.Errorf("%s does not marshal: %v", key, err)
			continue
		}
		round := map[string]any{}
		if err := yaml.Unmarshal(encoded, &round); err != nil {
			t.Errorf("%s does not round-trip: %v", key, err)
		}
	}
}
