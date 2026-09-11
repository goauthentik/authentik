package controller

import (
	"strings"
	"testing"
	"time"

	batchv1 "k8s.io/api/batch/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/util/validation"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"

	instancev1alpha1 "goauthentik.io/lifecycle/operator/api/v1alpha1"
)

const (
	name      = "authentik"
	namespace = "authentik"
	chartTag  = "2026.8.0"
	globalKey = "global"
)

func testScheme(t *testing.T) *runtime.Scheme {
	t.Helper()

	scheme := runtime.NewScheme()
	if err := clientgoscheme.AddToScheme(scheme); err != nil {
		t.Fatalf("failed to add client-go scheme: %v", err)
	}
	if err := instancev1alpha1.AddToScheme(scheme); err != nil {
		t.Fatalf("failed to add authentik scheme: %v", err)
	}
	return scheme
}

func testAuthentik(spec instancev1alpha1.AuthentikSpec) *instancev1alpha1.Authentik {
	return &instancev1alpha1.Authentik{
		Name:      name,
		Namespace: namespace,
		UID:       "11111111-2222-3333-4444-555555555555",
		Spec:      spec,
	}
}

func buildJob(t *testing.T, ak *instancev1alpha1.Authentik, version string) *batchv1.Job {
	t.Helper()

	r := &AuthentikReconciler{Scheme: testScheme(t)}
	job, err := r.buildMigrationJob(ak, version)
	if err != nil {
		t.Fatalf("buildMigrationJob: %v", err)
	}
	return job
}

func TestBuildMigrationJobRunsTheTargetVersionAgainstTheSameConfig(t *testing.T) {
	// The migration has to run the image the Deployments are about to move to,
	// against the same configuration Secret, or it would migrate the wrong
	// database or to the wrong schema.
	ak := testAuthentik(instancev1alpha1.AuthentikSpec{})
	job := buildJob(t, ak, "2026.8.1")

	if got, want := len(job.Spec.Template.Spec.Containers), 1; got != want {
		t.Fatalf("containers = %d, want %d", got, want)
	}
	container := job.Spec.Template.Spec.Containers[0]

	if want := "ghcr.io/goauthentik/server:2026.8.1"; container.Image != want {
		t.Errorf("image = %q, want %q", container.Image, want)
	}
	if want := strings.Join(instancev1alpha1.DefaultMigrationCommand, " "); strings.Join(container.Command, " ") != want {
		t.Errorf("command = %v, want %v", container.Command, instancev1alpha1.DefaultMigrationCommand)
	}
	if len(container.EnvFrom) == 0 || container.EnvFrom[0].SecretRef == nil ||
		container.EnvFrom[0].SecretRef.Name != name {
		t.Errorf("envFrom = %+v, want the authentik config Secret first", container.EnvFrom)
	}

	if job.Spec.Template.Spec.RestartPolicy != corev1.RestartPolicyNever {
		t.Errorf("restartPolicy = %q, want Never", job.Spec.Template.Spec.RestartPolicy)
	}
	if job.Namespace != namespace {
		t.Errorf("namespace = %q, want authentik", job.Namespace)
	}

	// Without an owner reference the Job would outlive the Authentik resource.
	owners := job.GetOwnerReferences()
	if len(owners) != 1 || owners[0].Kind != "Authentik" || owners[0].Controller == nil || !*owners[0].Controller {
		t.Errorf("ownerReferences = %+v, want a single controller reference to Authentik", owners)
	}
}

func TestBuildMigrationJobUsesTheExistingSecretWhenConfigured(t *testing.T) {
	ak := testAuthentik(instancev1alpha1.AuthentikSpec{
		Authentik: &instancev1alpha1.AuthentikConfigSpec{
			ExistingSecret: &instancev1alpha1.AuthentikExistingSecret{SecretName: "my-config"},
		},
	})
	job := buildJob(t, ak, chartTag)

	envFrom := job.Spec.Template.Spec.Containers[0].EnvFrom
	if len(envFrom) == 0 || envFrom[0].SecretRef == nil || envFrom[0].SecretRef.Name != "my-config" {
		t.Errorf("envFrom = %+v, want the my-config Secret", envFrom)
	}
}

func TestBuildMigrationJobInheritsWorkerScheduling(t *testing.T) {
	// A migration should land where the worker would, since it is the component
	// that normally runs them.
	ak := testAuthentik(instancev1alpha1.AuthentikSpec{
		Worker: &instancev1alpha1.WorkerSpec{
			NodeSelector:       map[string]string{"workload": name},
			ServiceAccountName: "authentik-worker",
			PriorityClassName:  "high",
			Tolerations: []corev1.Toleration{{
				Key: "dedicated", Operator: corev1.TolerationOpEqual, Value: name,
			}},
		},
	})
	job := buildJob(t, ak, chartTag)
	spec := job.Spec.Template.Spec

	if spec.NodeSelector["workload"] != name {
		t.Errorf("nodeSelector = %v", spec.NodeSelector)
	}
	if spec.ServiceAccountName != "authentik-worker" {
		t.Errorf("serviceAccountName = %q", spec.ServiceAccountName)
	}
	if spec.PriorityClassName != "high" {
		t.Errorf("priorityClassName = %q", spec.PriorityClassName)
	}
	if len(spec.Tolerations) != 1 {
		t.Errorf("tolerations = %v", spec.Tolerations)
	}
}

func TestBuildMigrationJobFallsBackToGlobalScheduling(t *testing.T) {
	ak := testAuthentik(instancev1alpha1.AuthentikSpec{
		Global: &instancev1alpha1.GlobalSpec{
			NodeSelector:      map[string]string{"zone": "a"},
			PriorityClassName: "global-high",
		},
	})
	spec := buildJob(t, ak, chartTag).Spec.Template.Spec

	if spec.NodeSelector["zone"] != "a" {
		t.Errorf("nodeSelector = %v, want the global value", spec.NodeSelector)
	}
	if spec.PriorityClassName != "global-high" {
		t.Errorf("priorityClassName = %q, want the global value", spec.PriorityClassName)
	}
}

func TestMigrationJobNameIsStableAndValid(t *testing.T) {
	ak := testAuthentik(instancev1alpha1.AuthentikSpec{})

	first := buildJob(t, ak, chartTag).Name
	second := buildJob(t, ak, chartTag).Name
	if first != second {
		t.Errorf("name is not stable: %q then %q", first, second)
	}
	if errs := validation.IsDNS1123Subdomain(first); len(errs) > 0 {
		t.Errorf("name %q is not a valid object name: %v", first, errs)
	}
}

func TestMigrationJobNameChangesWithTheVersion(t *testing.T) {
	// A new target version has to be a new attempt, otherwise the operator
	// would find the previous version's completed Job and open the gate
	// without having migrated.
	ak := testAuthentik(instancev1alpha1.AuthentikSpec{})
	if a, b := buildJob(t, ak, chartTag).Name, buildJob(t, ak, "2026.8.1").Name; a == b {
		t.Errorf("different versions produced the same Job name %q", a)
	}
}

func TestMigrationJobNameChangesWhenTheMigrationChanges(t *testing.T) {
	// Fixing a broken migration has to yield a fresh attempt, because a failed
	// Job is deliberately left in place.
	base := testAuthentik(instancev1alpha1.AuthentikSpec{})
	fixed := testAuthentik(instancev1alpha1.AuthentikSpec{
		Migrations: &instancev1alpha1.MigrationsSpec{Command: []string{"ak", "migrate", "--noinput"}},
	})

	if a, b := buildJob(t, base, chartTag).Name, buildJob(t, fixed, chartTag).Name; a == b {
		t.Errorf("changing the migration command did not change the Job name %q", a)
	}
}

func TestMigrationJobNameIgnoresUnrelatedChanges(t *testing.T) {
	// Scaling the server must not re-run migrations.
	base := testAuthentik(instancev1alpha1.AuthentikSpec{})
	scaled := testAuthentik(instancev1alpha1.AuthentikSpec{
		Server: &instancev1alpha1.ServerSpec{
			Replicas: new(int32(5)),
		},
	})

	if a, b := buildJob(t, base, chartTag).Name, buildJob(t, scaled, chartTag).Name; a != b {
		t.Errorf("a server replica change changed the Job name: %q vs %q", a, b)
	}
}

func TestMigrationJobNameFitsTheNameLimit(t *testing.T) {
	ak := testAuthentik(instancev1alpha1.AuthentikSpec{
		Global: &instancev1alpha1.GlobalSpec{
			FullnameOverride: strings.Repeat("a", 63),
		},
	})

	name := buildJob(t, ak, chartTag).Name
	if len(name) > 63 {
		t.Errorf("name is %d characters: %q", len(name), name)
	}
	if errs := validation.IsDNS1123Subdomain(name); len(errs) > 0 {
		t.Errorf("name %q is not a valid object name: %v", name, errs)
	}
}

func TestMigrationJobDefaults(t *testing.T) {
	job := buildJob(t, testAuthentik(instancev1alpha1.AuthentikSpec{}), chartTag)

	if job.Spec.BackoffLimit == nil || *job.Spec.BackoffLimit != instancev1alpha1.DefaultMigrationBackoffLimit {
		t.Errorf("backoffLimit = %v", job.Spec.BackoffLimit)
	}
	// Without a deadline a hung migration would block the rollout forever.
	if job.Spec.ActiveDeadlineSeconds == nil || *job.Spec.ActiveDeadlineSeconds != instancev1alpha1.DefaultMigrationDeadlineSeconds {
		t.Errorf("activeDeadlineSeconds = %v", job.Spec.ActiveDeadlineSeconds)
	}
	// A TTL keeps the logs readable for a while, then cleans up.
	if job.Spec.TTLSecondsAfterFinished == nil || *job.Spec.TTLSecondsAfterFinished != instancev1alpha1.DefaultMigrationTTLSeconds {
		t.Errorf("ttlSecondsAfterFinished = %v", job.Spec.TTLSecondsAfterFinished)
	}
}

func TestJobOutcome(t *testing.T) {
	cases := []struct {
		name       string
		conditions []batchv1.JobCondition
		want       migrationOutcome
	}{
		{"no conditions", nil, migrationRunning},
		{
			"complete",
			[]batchv1.JobCondition{{Type: batchv1.JobComplete, Status: corev1.ConditionTrue}},
			migrationSucceeded,
		},
		{
			"failed",
			[]batchv1.JobCondition{{Type: batchv1.JobFailed, Status: corev1.ConditionTrue}},
			migrationFailed,
		},
		{
			// A condition present but False must not be read as terminal.
			"complete but false",
			[]batchv1.JobCondition{{Type: batchv1.JobComplete, Status: corev1.ConditionFalse}},
			migrationRunning,
		},
		{
			"suspended",
			[]batchv1.JobCondition{{Type: batchv1.JobSuspended, Status: corev1.ConditionTrue}},
			migrationRunning,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			job := &batchv1.Job{Status: batchv1.JobStatus{Conditions: tc.conditions}}
			if got := jobOutcome(job); got != tc.want {
				t.Errorf("jobOutcome() = %v, want %v", got, tc.want)
			}
		})
	}
}

func TestJobFailureReasonPrefersTheMessage(t *testing.T) {
	job := &batchv1.Job{Status: batchv1.JobStatus{Conditions: []batchv1.JobCondition{{
		Type: batchv1.JobFailed, Status: corev1.ConditionTrue,
		Reason: "BackoffLimitExceeded", Message: "Job has reached the specified backoff limit",
	}}}}
	if got, want := jobFailureReason(job), "Job has reached the specified backoff limit"; got != want {
		t.Errorf("jobFailureReason() = %q, want %q", got, want)
	}

	job.Status.Conditions[0].Message = ""
	if got, want := jobFailureReason(job), "BackoffLimitExceeded"; got != want {
		t.Errorf("jobFailureReason() = %q, want %q", got, want)
	}
}

func TestLabelSafeVersion(t *testing.T) {
	cases := map[string]string{
		chartTag:                     chartTag,
		"gh-main-1756600000-abc1234": "gh-main-1756600000-abc1234",
		"-leading-and-trailing-":     "leading-and-trailing",
		"has/slashes:and@signs":      "has-slashes-and-signs",
		strings.Repeat("v", 100):     strings.Repeat("v", 63),
	}

	for version, want := range cases {
		got := instancev1alpha1.LabelSafeVersion(version)
		if got != want {
			t.Errorf("instancev1alpha1.LabelSafeVersion(%q) = %q, want %q", version, got, want)
		}
		if errs := validation.IsValidLabelValue(got); len(errs) > 0 {
			t.Errorf("instancev1alpha1.LabelSafeVersion(%q) = %q, which is not a valid label value: %v", version, got, errs)
		}
	}
}

func TestSkipApply(t *testing.T) {
	const hash = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
	interval := 5 * time.Minute

	installed := func(mutate func(*clusterState)) *clusterState {
		state := &clusterState{
			installed:   true,
			version:     chartTag,
			appliedHash: hash,
			lastApplied: time.Now(),
		}
		if mutate != nil {
			mutate(state)
		}
		return state
	}

	cases := []struct {
		name     string
		current  *clusterState
		hash     string
		wantSkip bool
	}{
		{
			name:     "unchanged and recent, so nothing to do",
			current:  installed(nil),
			hash:     hash,
			wantSkip: true,
		},
		{
			// This is the case that would loop: applying unconditionally
			// changes the objects, which changes status, which reconciles again.
			name:     "nothing installed yet",
			current:  &clusterState{},
			hash:     hash,
			wantSkip: false,
		},
		{
			name:     "desired state changed",
			current:  installed(nil),
			hash:     "0000000000000000000000000000000000000000000000000000000000000000",
			wantSkip: false,
		},
		{
			name:     "no hash recorded, e.g. adopted from a chart install",
			current:  installed(func(s *clusterState) { s.appliedHash = "" }),
			hash:     hash,
			wantSkip: false,
		},
		{
			name:     "not applied for a whole interval, so re-apply to correct drift",
			current:  installed(func(s *clusterState) { s.lastApplied = time.Now().Add(-10 * time.Minute) }),
			hash:     hash,
			wantSkip: false,
		},
		{
			name:     "no apply timestamp",
			current:  installed(func(s *clusterState) { s.lastApplied = time.Time{} }),
			hash:     hash,
			wantSkip: false,
		},
	}

	r := &AuthentikReconciler{}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			reason, skip := r.skipApply(tc.current, tc.hash, interval)
			if skip != tc.wantSkip {
				t.Errorf("skipApply() skip = %v, want %v (reason %q)", skip, tc.wantSkip, reason)
			}
			if skip && reason == "" {
				t.Error("skipApply() skipped without giving a reason")
			}
		})
	}
}

func TestImageTag(t *testing.T) {
	// Reading the tag off the running image is the fallback for an instance
	// adopted from a chart install, which carries none of the operator's
	// annotations.
	cases := map[string]string{
		"ghcr.io/goauthentik/server:2026.8.0":         "2026.8.0",
		"ghcr.io/goauthentik/server:gh-main-1-abc123": "gh-main-1-abc123",
		"busybox:1.37": "1.37",
		// A digest pins the image regardless of tag, so there is no version.
		"ghcr.io/goauthentik/server@sha256:aaaa":       "",
		"ghcr.io/goauthentik/server:2026.8.0@sha256:a": "",
		// A registry port must not be mistaken for a tag.
		"registry.example.com:5000/authentik": "",
		"ghcr.io/goauthentik/server":          "",
	}

	for image, want := range cases {
		if got := imageTag(image); got != want {
			t.Errorf("imageTag(%q) = %q, want %q", image, got, want)
		}
	}
}

func TestMigrationTroubleReasons(t *testing.T) {
	// These are the states a migration pod can sit in without the Job ever
	// reaching JobFailed, which is what makes them worth reporting.
	for _, reason := range []string{"ImagePullBackOff", "ErrImagePull", "InvalidImageName", "CrashLoopBackOff"} {
		if !stuckWaitingReasons[reason] {
			t.Errorf("%q should be treated as stuck", reason)
		}
	}
	for _, reason := range []string{"ContainerCreating", "PodInitializing", ""} {
		if stuckWaitingReasons[reason] {
			t.Errorf("%q should not be treated as stuck", reason)
		}
	}
}
