package controller

import (
	"cmp"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"maps"
	"slices"
	"strings"

	batchv1 "k8s.io/api/batch/v1"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/utils/ptr"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/log"

	instancev1alpha1 "goauthentik.io/lifecycle/operator/api/v1alpha1"
)

// migrationOutcome is where a migration Job has got to.
type migrationOutcome int

const (
	// migrationRunning means the Job exists and has not finished.
	migrationRunning migrationOutcome = iota
	// migrationSucceeded means the database is migrated to the target version.
	migrationSucceeded
	// migrationFailed means the Job exhausted its retries or hit its deadline.
	migrationFailed
)

// migrationJobName is the Job name for one migration attempt.
//
// The name is derived from the pod template rather than from the version alone,
// which is what makes a retry well defined. A failed Job is left in place, so
// reconciling again finds the same failure instead of restarting a migration
// that is genuinely broken. Changing anything the migration actually depends on
// -- the image, the command, the configuration Secret -- produces a different
// name and therefore a fresh attempt, while an unrelated change such as a
// replica count leaves the name alone and does not re-run migrations.
//
// The template is hashed rather than described because image tags contain
// characters that are not valid in object names, and because names are capped
// at 63 characters.
func migrationJobName(ak *instancev1alpha1.Authentik, template *corev1.PodTemplateSpec) (string, error) {
	encoded, err := json.Marshal(template)
	if err != nil {
		return "", fmt.Errorf("failed to hash the migration pod template: %w", err)
	}

	digest := sha256.Sum256(encoded)
	suffix := hex.EncodeToString(digest[:])[:8]

	prefix := ak.Fullname()
	// Leave room for "-migrate-" plus the 8-character digest.
	if max := 63 - len("-migrate-") - len(suffix); len(prefix) > max {
		prefix = strings.TrimSuffix(prefix[:max], "-")
	}
	return fmt.Sprintf("%s-migrate-%s", prefix, suffix), nil
}

// buildMigrationJob renders the Job that migrates the database to one version.
//
// It runs the same image the Deployments are about to move to, with the same
// configuration Secret, so it sees exactly the database the new code expects.
// Everything scheduling-related is inherited from the worker, on the grounds
// that a migration has the same placement requirements as the component that
// normally runs them.
func (r *AuthentikReconciler) buildMigrationJob(
	ak *instancev1alpha1.Authentik,
	version string,
) (*batchv1.Job, error) {
	spec := ak.Spec.Migrations
	if spec == nil {
		spec = &instancev1alpha1.MigrationsSpec{}
	}

	// Empty values for absent sections keep the fallbacks below from each
	// needing their own nil check.
	global := ak.Spec.Global
	if global == nil {
		global = &instancev1alpha1.GlobalSpec{}
	}
	worker := instancev1alpha1.ComponentSpec{}
	if ak.Spec.Worker != nil {
		worker = ak.Spec.Worker.ComponentSpec
	}

	backoffLimit := ptr.Deref(spec.BackoffLimit, instancev1alpha1.DefaultMigrationBackoffLimit)
	deadline := ptr.Deref(spec.ActiveDeadlineSeconds, instancev1alpha1.DefaultMigrationDeadlineSeconds)
	ttl := ptr.Deref(spec.TTLSecondsAfterFinished, instancev1alpha1.DefaultMigrationTTLSeconds)

	resources := corev1.ResourceRequirements{}
	switch {
	case spec.Resources != nil:
		resources = *spec.Resources
	case worker.Resources != nil:
		resources = *worker.Resources
	}

	labels := map[string]string{
		"app.kubernetes.io/name":       ak.BaseName(),
		"app.kubernetes.io/instance":   ak.ReleaseName(),
		"app.kubernetes.io/component":  instancev1alpha1.MigrateCommand,
		"app.kubernetes.io/part-of":    instancev1alpha1.DefaultName,
		"app.kubernetes.io/managed-by": instancev1alpha1.ManagedByLabelValue,
		// Makes it obvious which Job belongs to which rollout, and lets the
		// operator find its own Jobs without parsing names.
		versionKey: instancev1alpha1.LabelSafeVersion(version),
	}
	maps.Copy(labels, global.AdditionalLabels)
	if spec.Metadata != nil {
		maps.Copy(labels, spec.Metadata.Labels)
	}

	annotations := map[string]string{versionKey: version}
	podAnnotations := maps.Clone(global.PodAnnotations)
	if spec.Metadata != nil {
		maps.Copy(annotations, spec.Metadata.Annotations)
		if len(spec.Metadata.Annotations) > 0 {
			if podAnnotations == nil {
				podAnnotations = map[string]string{}
			}
			maps.Copy(podAnnotations, spec.Metadata.Annotations)
		}
	}

	// The configuration Secret has to come first, so a caller's own envFrom can
	// override individual keys from it.
	envFrom := make([]corev1.EnvFromSource, 0, 1+len(global.EnvFrom)+len(worker.EnvFrom))
	envFrom = append(envFrom, corev1.EnvFromSource{
		SecretRef: &corev1.SecretEnvSource{
			Name: ak.ConfigSecretName(),
		},
	})
	envFrom = append(envFrom, global.EnvFrom...)
	envFrom = append(envFrom, worker.EnvFrom...)

	env := slices.Concat(global.Env, worker.Env)
	volumeMounts := slices.Concat(global.VolumeMounts, worker.VolumeMounts)
	volumes := slices.Concat(global.Volumes, worker.Volumes)

	// Each of these falls back to the global value when the worker does not
	// set it.
	pullSecrets := worker.ImagePullSecrets
	if len(pullSecrets) == 0 {
		pullSecrets = global.ImagePullSecrets
	}
	nodeSelector := worker.NodeSelector
	if len(nodeSelector) == 0 {
		nodeSelector = global.NodeSelector
	}
	tolerations := worker.Tolerations
	if len(tolerations) == 0 {
		tolerations = global.Tolerations
	}
	securityContext := cmp.Or(worker.SecurityContext, global.SecurityContext)
	var pullPolicy corev1.PullPolicy
	if worker.Image != nil {
		pullPolicy = worker.Image.PullPolicy
	}
	if pullPolicy == "" && global.Image != nil {
		pullPolicy = global.Image.PullPolicy
	}

	template := corev1.PodTemplateSpec{
		Labels:      labels,
		Annotations: podAnnotations,
		Spec: corev1.PodSpec{
			// A migration either completes or it does not; retrying the whole
			// pod is the Job controller's business.
			RestartPolicy:    corev1.RestartPolicyNever,
			ImagePullSecrets: pullSecrets,
			Containers: []corev1.Container{{
				Name:            instancev1alpha1.MigrateCommand,
				Image:           ak.ImageRef(version),
				ImagePullPolicy: pullPolicy,
				Command:         ak.MigrationCommand(),
				Env:             env,
				EnvFrom:         envFrom,
				VolumeMounts:    volumeMounts,
				Resources:       resources,
				SecurityContext: worker.ContainerSecurityContext,
			}},
			Volumes:            volumes,
			SecurityContext:    securityContext,
			ServiceAccountName: worker.ServiceAccountName,
			NodeSelector:       nodeSelector,
			Tolerations:        tolerations,
			Affinity:           worker.Affinity,
			PriorityClassName:  cmp.Or(worker.PriorityClassName, global.PriorityClassName),
			HostAliases:        global.HostAliases,
		},
	}

	name, err := migrationJobName(ak, &template)
	if err != nil {
		return nil, err
	}

	job := &batchv1.Job{
		Name:        name,
		Namespace:   ak.TargetNamespace(),
		Labels:      labels,
		Annotations: annotations,
		Spec: batchv1.JobSpec{
			BackoffLimit:            &backoffLimit,
			ActiveDeadlineSeconds:   &deadline,
			TTLSecondsAfterFinished: &ttl,
			Template:                template,
		},
	}

	if err := ctrl.SetControllerReference(ak, job, r.Scheme); err != nil {
		return nil, fmt.Errorf("failed to set controller reference on migration Job: %w", err)
	}

	return job, nil
}

// reconcileMigration makes sure a migration Job for the target version exists
// and reports where it has got to.
func (r *AuthentikReconciler) reconcileMigration(
	ctx context.Context,
	ak *instancev1alpha1.Authentik,
	version string,
) (migrationOutcome, *batchv1.Job, error) {
	desired, err := r.buildMigrationJob(ak, version)
	if err != nil {
		return migrationFailed, nil, err
	}

	existing := &batchv1.Job{}
	key := types.NamespacedName{Namespace: desired.Namespace, Name: desired.Name}

	switch err := r.Get(ctx, key, existing); {
	case apierrors.IsNotFound(err):
		if err := r.Create(ctx, desired); err != nil {
			if apierrors.IsAlreadyExists(err) {
				// Lost a race with another reconcile; pick it up next pass.
				return migrationRunning, nil, nil
			}
			return migrationFailed, nil, fmt.Errorf("failed to create migration Job %q: %w", desired.Name, err)
		}
		return migrationRunning, desired, nil
	case err != nil:
		return migrationFailed, nil, fmt.Errorf("failed to read migration Job %q: %w", desired.Name, err)
	}

	// A Job's pod template is immutable, so the existing Job is never updated.
	// It is either the Job for this version, in which case its result stands,
	// or it is a stale Job for a version that is no longer targeted, in which
	// case it will be garbage collected via its owner reference or its TTL.
	return jobOutcome(existing), existing, nil
}

func jobOutcome(job *batchv1.Job) migrationOutcome {
	for _, condition := range job.Status.Conditions {
		if condition.Status != corev1.ConditionTrue {
			continue
		}
		switch condition.Type {
		case batchv1.JobComplete:
			return migrationSucceeded
		case batchv1.JobFailed:
			return migrationFailed
		}
	}
	return migrationRunning
}

// jobFailureReason summarizes why a Job failed, for the resource's conditions.
func jobFailureReason(job *batchv1.Job) string {
	for _, condition := range job.Status.Conditions {
		if condition.Type == batchv1.JobFailed && condition.Status == corev1.ConditionTrue {
			if condition.Message != "" {
				return condition.Message
			}
			return condition.Reason
		}
	}
	return "the migration Job failed"
}

// stuckWaitingReasons are container waiting reasons that will not clear on
// their own within a useful timeframe. A Job whose pod is in one of these never
// reaches JobFailed, so without reporting them the rollout would sit held for
// activeDeadlineSeconds -- up to an hour by default -- with the status claiming
// the migration is simply "running".
var stuckWaitingReasons = map[string]bool{
	"ImagePullBackOff":           true,
	"ErrImagePull":               true,
	"InvalidImageName":           true,
	"CreateContainerConfigError": true,
	"CreateContainerError":       true,
	"CrashLoopBackOff":           true,
}

// migrationTrouble looks for a reason the migration Job is not making progress.
// It returns an empty string when the Job looks healthy.
func (r *AuthentikReconciler) migrationTrouble(ctx context.Context, job *batchv1.Job) string {
	if job == nil {
		return ""
	}

	pods := &corev1.PodList{}
	err := r.List(ctx, pods,
		client.InNamespace(job.Namespace),
		client.MatchingLabels{"batch.kubernetes.io/job-name": job.Name},
	)
	if err != nil {
		// Not being able to look is not itself a problem worth reporting on the
		// resource; the Job's own conditions still govern the gate.
		logf.FromContext(ctx).V(1).Info("Could not list migration Job pods", "error", err)
		return ""
	}

	for _, pod := range pods.Items {
		for _, condition := range pod.Status.Conditions {
			if condition.Type == corev1.PodScheduled &&
				condition.Status == corev1.ConditionFalse &&
				condition.Reason == corev1.PodReasonUnschedulable {
				return fmt.Sprintf("pod %s cannot be scheduled: %s", pod.Name, condition.Message)
			}
		}

		statuses := slices.Concat(pod.Status.InitContainerStatuses, pod.Status.ContainerStatuses)
		for _, status := range statuses {
			waiting := status.State.Waiting
			if waiting != nil && stuckWaitingReasons[waiting.Reason] {
				return fmt.Sprintf("pod %s is stuck in %s: %s", pod.Name, waiting.Reason, waiting.Message)
			}
		}
	}

	return ""
}
