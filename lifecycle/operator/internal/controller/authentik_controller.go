/*
Copyright 2026.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package controller

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	batchv1 "k8s.io/api/batch/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/equality"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/tools/events"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/builder"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"

	akv1alpha1 "goauthentik.io/lifecycle/operator/api/v1alpha1"
	"goauthentik.io/lifecycle/operator/internal/apply"
	"goauthentik.io/lifecycle/operator/internal/resources"
	"goauthentik.io/lifecycle/operator/internal/version"
)

const (
	// finalizer holds the Authentik resource open long enough to delete the
	// cluster-scoped objects, which cannot carry an owner reference back to a
	// namespaced resource and so are not garbage collected with it.
	finalizer = "instance.goauthentik.io/finalizer"

	// versionLabel records which authentik version an object belongs to.
	versionLabel = "instance.goauthentik.io/version"

	// versionAnnotation carries the unmodified image tag, since a tag is not
	// always a valid label value.
	versionAnnotation = "instance.goauthentik.io/version"

	// appliedHashAnnotation records on the server Deployment which desired
	// state produced it.
	//
	// It lives on a cluster object rather than only in status because status is
	// read back through an informer cache that can lag by a moment, which is
	// long enough for two reconciles in a row to both decide work is needed.
	appliedHashAnnotation = "instance.goauthentik.io/applied-hash"

	// requeueOnFailure is how long to wait before retrying after a failure that
	// retrying immediately would not fix.
	requeueOnFailure = time.Minute

	// requeueWhileMigrating is how often to check back on a running migration.
	requeueWhileMigrating = 10 * time.Second
)

// AuthentikReconciler reconciles an Authentik object by building the
// Kubernetes objects that make up an authentik installation and applying them,
// gating version changes behind a database migration Job.
type AuthentikReconciler struct {
	client.Client
	Scheme   *runtime.Scheme
	Recorder events.EventRecorder

	// Applier applies the built objects and prunes the ones no longer wanted.
	Applier *apply.Applier

	// Resolver turns a tracked branch into an image tag. Optional; without it
	// autoUpdate cannot be used.
	Resolver *version.RegistryResolver
}

// +kubebuilder:rbac:groups=instance.goauthentik.io,resources=authentiks,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=instance.goauthentik.io,resources=authentiks/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=instance.goauthentik.io,resources=authentiks/finalizers,verbs=update
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch

// The operator creates and prunes each of these on the user's behalf.
// +kubebuilder:rbac:groups="",resources=secrets;configmaps;services;serviceaccounts;persistentvolumeclaims,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups="",resources=pods,verbs=get;list;watch
// +kubebuilder:rbac:groups="",resources=pods/log,verbs=get
// +kubebuilder:rbac:groups=apps,resources=deployments;statefulsets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=batch,resources=jobs,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=networking.k8s.io,resources=ingresses,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=autoscaling,resources=horizontalpodautoscalers,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=policy,resources=poddisruptionbudgets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=monitoring.coreos.com,resources=servicemonitors;prometheusrules,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=gateway.networking.k8s.io,resources=httproutes,verbs=get;list;watch;create;update;patch;delete

// The worker manages Kubernetes outposts, which means the operator grants it
// RBAC. Granting rights is only allowed if the granter holds them, so the
// operator needs everything it hands to the worker.
// +kubebuilder:rbac:groups=rbac.authorization.k8s.io,resources=roles;rolebindings;clusterroles;clusterrolebindings,verbs=get;list;watch;create;update;patch;delete;bind;escalate
// +kubebuilder:rbac:groups=traefik.containo.us;traefik.io,resources=middlewares,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apiextensions.k8s.io,resources=customresourcedefinitions,verbs=get;list;watch

// Reconcile drives one Authentik resource towards its desired state.
//
// The order is the point of the operator:
//
//  1. resolve the authentik version to deploy, from the spec or the registry
//  2. on an upgrade, run the database migrations to completion in a Job
//  3. only then apply the Deployments
//
// Applying everything at once, as installing the chart does, starts new pods
// that migrate the database while old pods are still serving the old schema.
func (r *AuthentikReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := logf.FromContext(ctx)

	ak := &akv1alpha1.Authentik{}
	if err := r.Get(ctx, req.NamespacedName, ak); err != nil {
		if apierrors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, fmt.Errorf("failed to read Authentik: %w", err)
	}

	if !ak.DeletionTimestamp.IsZero() {
		return r.reconcileDelete(ctx, ak)
	}

	if !controllerutil.ContainsFinalizer(ak, finalizer) {
		patch := client.MergeFrom(ak.DeepCopy())
		controllerutil.AddFinalizer(ak, finalizer)
		if err := r.Patch(ctx, ak, patch); err != nil {
			return ctrl.Result{}, fmt.Errorf("failed to add finalizer: %w", err)
		}
	}

	status := ak.Status.DeepCopy()
	status.ObservedGeneration = ak.Generation

	result, err := r.reconcileInstance(ctx, ak, status)

	// Status is written even when reconciliation failed, so the conditions
	// explain why rather than going stale.
	if statusErr := r.patchStatus(ctx, ak, status); statusErr != nil {
		if err == nil {
			return ctrl.Result{}, statusErr
		}
		log.Error(statusErr, "Failed to update status")
	}

	return result, err
}

// reconcileInstance is the main path, split out so its caller can always write
// status.
func (r *AuthentikReconciler) reconcileInstance(
	ctx context.Context,
	ak *akv1alpha1.Authentik,
	status *akv1alpha1.AuthentikStatus,
) (ctrl.Result, error) {
	log := logf.FromContext(ctx)

	targetVersion, err := r.resolveVersion(ctx, ak, status)
	if err != nil {
		r.fail(status, ak, akv1alpha1.ConditionReady, "VersionResolutionFailed", err.Error())
		r.event(ak, corev1.EventTypeWarning, "VersionResolutionFailed", "ResolveVersion", err.Error())
		return ctrl.Result{RequeueAfter: requeueOnFailure}, nil
	}
	status.ResolvedImage = ak.ImageRef(targetVersion)

	resourceBuilder := &resources.Builder{Authentik: ak, Version: targetVersion}
	desired, err := resourceBuilder.Build()
	if err != nil {
		// A spec the builders reject will not build on a retry either.
		r.fail(status, ak, akv1alpha1.ConditionDeployed, "InvalidSpec", err.Error())
		return ctrl.Result{}, reconcile.TerminalError(err)
	}

	desiredHash, err := akv1alpha1.DesiredStateHash(&ak.Spec, targetVersion)
	if err != nil {
		r.fail(status, ak, akv1alpha1.ConditionDeployed, "InvalidSpec", err.Error())
		return ctrl.Result{}, reconcile.TerminalError(err)
	}

	// What is already running decides whether this is a first install or an
	// upgrade, and from which version. Read from the cluster rather than from
	// status, which is written by this controller and can lag behind it.
	current, err := r.currentState(ctx, ak)
	if err != nil {
		r.fail(status, ak, akv1alpha1.ConditionDeployed, "ClusterReadFailed", err.Error())
		return ctrl.Result{}, err
	}

	// A first install is exempt from the migration gate: there is no older
	// authentik to be inconsistent with, and the configuration Secret the Job
	// would read its database credentials from does not exist yet. The server
	// and worker migrate on startup instead.
	switch {
	case !current.installed:
		status.MigratedVersion = targetVersion
		status.SetCondition(akv1alpha1.ConditionMigrated, string(metav1.ConditionTrue),
			"InitialInstall", "A first install migrates on startup, no migration Job was needed", ak.Generation)

	case !ak.MigrationsEnabled():
		status.MigratedVersion = targetVersion
		status.SetCondition(akv1alpha1.ConditionMigrated, string(metav1.ConditionTrue),
			"Disabled", "Migration gating is disabled, authentik migrates on startup", ak.Generation)

	case current.version == targetVersion:
		status.MigratedVersion = targetVersion
		status.SetCondition(akv1alpha1.ConditionMigrated, string(metav1.ConditionTrue),
			"UpToDate", fmt.Sprintf("Database is migrated to %s", targetVersion), ak.Generation)

	default:
		if done, result := r.runMigrationGate(ctx, ak, status, targetVersion); !done {
			return result, nil
		}
	}

	// Re-applying unconditionally would loop: an apply changes the objects,
	// which changes this resource's status, which is a watch event, which
	// reconciles again. The desired state is still re-applied once per
	// reconcile interval so that drift is corrected.
	if reason, skip := r.skipApply(current, desiredHash, ak.ReconcileInterval()); skip {
		log.V(1).Info("Desired state is already applied, skipping", "reason", reason)
		return r.ready(ak, status, targetVersion)
	}

	status.Phase = akv1alpha1.PhaseDeploying
	status.SetCondition(akv1alpha1.ConditionProgressing, string(metav1.ConditionTrue),
		"Applying", fmt.Sprintf("Applying authentik %s", targetVersion), ak.Generation)

	if !current.installed {
		r.event(ak, corev1.EventTypeNormal, "Installing", "Install",
			fmt.Sprintf("Installing authentik %s", targetVersion))
	} else if current.version != targetVersion {
		r.event(ak, corev1.EventTypeNormal, "Upgrading", "Upgrade",
			fmt.Sprintf("Upgrading authentik from %s to %s", current.version, targetVersion))
	}

	// The hash rides along on the server Deployment, so the next reconcile can
	// tell an unchanged desired state from a changed one without trusting status.
	annotateAppliedHash(desired, resourceBuilder.ServerName(), desiredHash, targetVersion)

	applied, err := r.Applier.Apply(ctx, ak, desired)
	if err != nil {
		r.fail(status, ak, akv1alpha1.ConditionDeployed, "ApplyFailed", err.Error())
		r.event(ak, corev1.EventTypeWarning, "ApplyFailed", "Apply", err.Error())
		return ctrl.Result{RequeueAfter: requeueOnFailure}, nil
	}

	pruned := []apply.ObjectKey{}
	if ak.PruneEnabled() {
		pruned, err = r.Applier.Prune(ctx, ak.TargetNamespace(), ak.OwnerSelector(), applied.Applied)
		if err != nil {
			r.fail(status, ak, akv1alpha1.ConditionDeployed, "PruneFailed", err.Error())
			return ctrl.Result{RequeueAfter: requeueOnFailure}, nil
		}
	}

	now := metav1.Now()
	status.Applied = &akv1alpha1.AppliedStatus{
		Objects:       int32(len(applied.Applied)),
		Pruned:        int32(len(pruned)),
		Skipped:       objectKeyStrings(applied.Skipped),
		LastAppliedAt: &now,
	}
	status.DeployedVersion = targetVersion
	status.AppliedHash = desiredHash
	status.SetCondition(akv1alpha1.ConditionDeployed, string(metav1.ConditionTrue),
		"Applied", fmt.Sprintf("Applied %d objects", len(applied.Applied)), ak.Generation)

	if len(applied.Skipped) > 0 {
		r.event(ak, corev1.EventTypeWarning, "KindNotInstalled", "Apply",
			fmt.Sprintf("Skipped %d object(s) whose kind is not installed in this cluster: %v",
				len(applied.Skipped), objectKeyStrings(applied.Skipped)))
	}

	log.Info("Applied the desired state", "version", targetVersion,
		"objects", len(applied.Applied), "pruned", len(pruned), "skipped", len(applied.Skipped))

	return r.ready(ak, status, targetVersion)
}

// ready reports the instance as ready and schedules the next drift check.
func (r *AuthentikReconciler) ready(
	ak *akv1alpha1.Authentik,
	status *akv1alpha1.AuthentikStatus,
	targetVersion string,
) (ctrl.Result, error) {
	status.Phase = akv1alpha1.PhaseReady
	status.SetCondition(akv1alpha1.ConditionReady, string(metav1.ConditionTrue),
		"Deployed", fmt.Sprintf("authentik %s is deployed", targetVersion), ak.Generation)
	status.SetCondition(akv1alpha1.ConditionProgressing, string(metav1.ConditionFalse),
		"Deployed", "The desired state is applied", ak.Generation)
	meta.RemoveStatusCondition(&status.Conditions, akv1alpha1.ConditionDegraded)

	return ctrl.Result{RequeueAfter: r.requeueInterval(ak)}, nil
}

// clusterState is what is already running, read from the cluster.
type clusterState struct {
	// installed is true once the server Deployment exists, which is what makes
	// a reconcile an upgrade rather than a first install.
	installed bool
	// version is the image tag the running server deploys.
	version string
	// appliedHash is the desired-state fingerprint of the last apply.
	appliedHash string
	// lastApplied is when the server Deployment was last written.
	lastApplied time.Time
}

// currentState reads what is deployed from the server Deployment, which is the
// one object that always exists for a running instance.
func (r *AuthentikReconciler) currentState(ctx context.Context, ak *akv1alpha1.Authentik) (*clusterState, error) {
	// Version does not matter for a lookup; only the name is needed.
	resourceBuilder := &resources.Builder{Authentik: ak}

	deployment := &appsv1.Deployment{}
	key := types.NamespacedName{Namespace: ak.TargetNamespace(), Name: resourceBuilder.ServerName()}
	if err := r.Get(ctx, key, deployment); err != nil {
		if apierrors.IsNotFound(err) {
			return &clusterState{}, nil
		}
		return nil, fmt.Errorf("failed to read the server Deployment: %w", err)
	}

	state := &clusterState{
		installed:   true,
		appliedHash: deployment.Annotations[appliedHashAnnotation],
		lastApplied: deployment.CreationTimestamp.Time,
	}
	if annotated := deployment.Annotations[versionAnnotation]; annotated != "" {
		state.version = annotated
	}
	// Fall back to the image itself, so an instance adopted from a chart
	// install -- which carries none of these annotations -- still reports the
	// version it is running and is correctly seen as an upgrade.
	if state.version == "" && len(deployment.Spec.Template.Spec.Containers) > 0 {
		state.version = imageTag(deployment.Spec.Template.Spec.Containers[0].Image)
	}

	for _, condition := range deployment.Status.Conditions {
		if condition.Type == appsv1.DeploymentProgressing {
			state.lastApplied = condition.LastUpdateTime.Time
		}
	}

	return state, nil
}

// skipApply decides whether the apply can be left out of this reconcile.
//
// Applying is skipped only when the cluster is genuinely already in the desired
// state and was written recently. Anything else -- a changed spec, a newly
// resolved version, a fresh install, an instance not touched for a whole
// reconcile interval -- applies.
func (r *AuthentikReconciler) skipApply(
	current *clusterState,
	desiredHash string,
	interval time.Duration,
) (string, bool) {
	if !current.installed {
		return "", false
	}
	if current.appliedHash == "" || current.appliedHash != desiredHash {
		return "", false
	}
	// Re-apply periodically so that a hand-edited object is put back.
	if current.lastApplied.IsZero() || time.Since(current.lastApplied) >= interval {
		return "", false
	}
	return "the desired state hash is unchanged and was applied recently", true
}

// runMigrationGate holds the rollout until the database is migrated to the
// target version. It reports whether the gate is open.
func (r *AuthentikReconciler) runMigrationGate(
	ctx context.Context,
	ak *akv1alpha1.Authentik,
	status *akv1alpha1.AuthentikStatus,
	targetVersion string,
) (bool, ctrl.Result) {
	log := logf.FromContext(ctx)

	outcome, job, err := r.reconcileMigration(ctx, ak, targetVersion)
	if err != nil {
		r.fail(status, ak, akv1alpha1.ConditionMigrated, "MigrationJobError", err.Error())
		return false, ctrl.Result{RequeueAfter: requeueOnFailure}
	}

	if job != nil {
		status.MigrationJob = job.Name
	}

	switch outcome {
	case migrationSucceeded:
		log.Info("Database migration completed", "job", status.MigrationJob, "version", targetVersion)
		r.event(ak, corev1.EventTypeNormal, "Migrated", "Migrate",
			fmt.Sprintf("Database migrated to authentik %s", targetVersion))
		status.MigratedVersion = targetVersion
		status.SetCondition(akv1alpha1.ConditionMigrated, string(metav1.ConditionTrue),
			"MigrationSucceeded", fmt.Sprintf("Database is migrated to %s", targetVersion), ak.Generation)
		return true, ctrl.Result{}

	case migrationFailed:
		reason := jobFailureReason(job)
		log.Info("Database migration failed, holding back the rollout", "job", status.MigrationJob, "reason", reason)

		// The Deployments are deliberately left alone. A failed migration means
		// the new version cannot run against this database, and rolling it out
		// anyway would take authentik down.
		//
		// The failed Job is left in place too. Its pods have already been
		// retried up to backoffLimit times, so the failure is not transient, and
		// deleting the Job would only restart a migration that is broken while
		// flapping the conditions on every pass. Its logs stay readable until
		// ttlSecondsAfterFinished, and fixing anything the migration depends on
		// yields a differently-named Job, which is a fresh attempt.
		r.fail(status, ak, akv1alpha1.ConditionMigrated, "MigrationFailed", reason)
		if previous := meta.FindStatusCondition(ak.Status.Conditions, akv1alpha1.ConditionMigrated); previous == nil ||
			previous.Reason != "MigrationFailed" {
			r.event(ak, corev1.EventTypeWarning, "MigrationFailed", "Migrate",
				fmt.Sprintf("Migration to authentik %s failed, authentik %s is left running: %s",
					targetVersion, status.DeployedVersion, reason))
		}
		return false, ctrl.Result{RequeueAfter: requeueOnFailure}

	default:
		status.Phase = akv1alpha1.PhaseMigrating

		// A Job whose pod cannot start never reaches JobFailed, so it would
		// otherwise sit here until activeDeadlineSeconds with the status saying
		// only that a migration is running.
		reason, message := "MigrationRunning", fmt.Sprintf("Migrating the database to %s", targetVersion)
		if trouble := r.migrationTrouble(ctx, job); trouble != "" {
			reason = "MigrationStuck"
			message = fmt.Sprintf("Migration to %s is not progressing: %s", targetVersion, trouble)

			// Only announce it the first time, so a stuck migration does not
			// emit an event on every poll.
			if existing := meta.FindStatusCondition(status.Conditions, akv1alpha1.ConditionMigrated); existing == nil ||
				existing.Reason != reason || existing.Message != message {
				log.Info("Migration Job is not progressing", "job", status.MigrationJob, "reason", trouble)
				r.event(ak, corev1.EventTypeWarning, "MigrationStuck", "Migrate", message)
			}
		}

		status.SetCondition(akv1alpha1.ConditionMigrated, string(metav1.ConditionFalse),
			reason, message, ak.Generation)
		status.SetCondition(akv1alpha1.ConditionProgressing, string(metav1.ConditionTrue),
			"Migrating", fmt.Sprintf("Waiting for migration Job %s", status.MigrationJob), ak.Generation)

		// The previously deployed version is still serving, so Ready describes
		// that rather than carrying over a stale failure from an earlier
		// attempt. Degraded is dropped for the same reason: this attempt has
		// not failed.
		status.SetCondition(akv1alpha1.ConditionReady, string(metav1.ConditionTrue),
			"UpgradePending", fmt.Sprintf("authentik %s is deployed, waiting to upgrade to %s",
				status.DeployedVersion, targetVersion), ak.Generation)
		meta.RemoveStatusCondition(&status.Conditions, akv1alpha1.ConditionDegraded)
		return false, ctrl.Result{RequeueAfter: requeueWhileMigrating}
	}
}

// resolveVersion decides which authentik image tag to deploy.
func (r *AuthentikReconciler) resolveVersion(
	ctx context.Context,
	ak *akv1alpha1.Authentik,
	status *akv1alpha1.AuthentikStatus,
) (string, error) {
	if !ak.AutoUpdateEnabled() {
		if tag := ak.ConfiguredTag(); tag != "" {
			return tag, nil
		}
		return "", errors.New("global.image.tag is required unless autoUpdate is enabled")
	}

	if ak.AutoUpdateTagStrategy() == akv1alpha1.TagStrategyBranch {
		return version.BranchTag(ak.Spec.AutoUpdate.Branch), nil
	}

	// Only poll the registry when the interval has elapsed. Without this every
	// drift-correcting reconcile would be a registry request.
	if status.LastResolvedAt != nil && status.DeployedVersion != "" {
		if elapsed := time.Since(status.LastResolvedAt.Time); elapsed < ak.AutoUpdateInterval() {
			return status.DeployedVersion, nil
		}
	}

	if r.Resolver == nil {
		return "", errors.New("autoUpdate is enabled but no version resolver is configured")
	}

	credential, err := r.registryCredential(ctx, ak)
	if err != nil {
		return "", err
	}

	result, err := r.Resolver.ResolveNewest(ctx, version.Request{
		Repository: ak.AutoUpdateRepository(),
		Branch:     ak.Spec.AutoUpdate.Branch,
		Credential: credential,
	})
	if err != nil {
		// Falling back to the deployed version keeps authentik running when the
		// registry is unreachable; only a first install has nothing to fall
		// back to.
		if status.DeployedVersion != "" {
			logf.FromContext(ctx).Error(err, "Failed to resolve the newest build, keeping the deployed version",
				"branch", ak.Spec.AutoUpdate.Branch, "version", status.DeployedVersion)
			r.event(ak, corev1.EventTypeWarning, "VersionResolutionFailed", "ResolveVersion",
				fmt.Sprintf("Keeping authentik %s: %v", status.DeployedVersion, err))
			return status.DeployedVersion, nil
		}
		return "", err
	}

	now := metav1.Now()
	status.LastResolvedAt = &now

	if result.Tag != status.DeployedVersion {
		logf.FromContext(ctx).Info("Resolved a new build for the tracked branch",
			"branch", ak.Spec.AutoUpdate.Branch, "tag", result.Tag, "commit", result.Commit,
			"buildTime", result.BuildTime)
	}

	return result.Tag, nil
}

// registryCredential reads the registry credentials from the configured pull
// secret, if there is one.
func (r *AuthentikReconciler) registryCredential(
	ctx context.Context,
	ak *akv1alpha1.Authentik,
) (version.Credential, error) {
	if ak.Spec.AutoUpdate == nil || ak.Spec.AutoUpdate.PullSecret == nil {
		return version.Credential{}, nil
	}

	name := ak.Spec.AutoUpdate.PullSecret.Name
	secret := &corev1.Secret{}
	key := types.NamespacedName{Namespace: ak.Namespace, Name: name}
	if err := r.Get(ctx, key, secret); err != nil {
		return version.Credential{}, fmt.Errorf("failed to read pull secret %q: %w", name, err)
	}

	repository, err := version.ParseReference(ak.AutoUpdateRepository())
	if err != nil {
		return version.Credential{}, fmt.Errorf("failed to parse repository %q: %w", ak.AutoUpdateRepository(), err)
	}

	credential, err := credentialFromDockerConfig(secret, repository.Registry)
	if err != nil {
		return version.Credential{}, fmt.Errorf("failed to read credentials for %q from Secret %q: %w",
			repository.Registry, name, err)
	}

	return credential, nil
}

// reconcileDelete removes what garbage collection cannot, then releases the
// finalizer.
func (r *AuthentikReconciler) reconcileDelete(
	ctx context.Context,
	ak *akv1alpha1.Authentik,
) (ctrl.Result, error) {
	log := logf.FromContext(ctx)

	if !controllerutil.ContainsFinalizer(ak, finalizer) {
		return ctrl.Result{}, nil
	}

	// Owner references take care of the namespaced objects. The cluster-scoped
	// RBAC cannot carry one, so it is deleted here.
	log.Info("Deleting the cluster-scoped objects", "instance", ak.Name)
	if err := r.Applier.DeleteClusterScoped(ctx, ak.OwnerSelector()); err != nil {
		r.event(ak, corev1.EventTypeWarning, "CleanupFailed", "Delete", err.Error())
		return ctrl.Result{RequeueAfter: requeueOnFailure}, err
	}

	// Objects in another namespace are not garbage collected either, because a
	// cross-namespace owner reference is not allowed.
	if ak.TargetNamespace() != ak.Namespace {
		if _, err := r.Applier.Prune(ctx, ak.TargetNamespace(), ak.OwnerSelector(), nil); err != nil {
			return ctrl.Result{RequeueAfter: requeueOnFailure}, err
		}
	}

	patch := client.MergeFrom(ak.DeepCopy())
	controllerutil.RemoveFinalizer(ak, finalizer)
	if err := r.Patch(ctx, ak, patch); err != nil {
		return ctrl.Result{}, fmt.Errorf("failed to remove finalizer: %w", err)
	}

	return ctrl.Result{}, nil
}

// requeueInterval is how long to wait before re-applying the desired state.
// With autoUpdate on, whichever of the two intervals is shorter wins, so
// polling the registry is not delayed by a long reconcile interval.
func (r *AuthentikReconciler) requeueInterval(ak *akv1alpha1.Authentik) time.Duration {
	interval := ak.ReconcileInterval()
	if ak.AutoUpdateEnabled() {
		if pollInterval := ak.AutoUpdateInterval(); pollInterval < interval {
			interval = pollInterval
		}
	}
	return interval
}

// annotateAppliedHash stamps the desired-state hash and the version onto the
// server Deployment, which is where the next reconcile reads them from.
func annotateAppliedHash(desired []client.Object, serverName, hash, tag string) {
	for _, object := range desired {
		if object.GetName() != serverName {
			continue
		}
		if _, ok := object.(*appsv1.Deployment); !ok {
			continue
		}

		annotations := object.GetAnnotations()
		if annotations == nil {
			annotations = map[string]string{}
		}
		annotations[appliedHashAnnotation] = hash
		annotations[versionAnnotation] = tag
		object.SetAnnotations(annotations)
		return
	}
}

// imageTag extracts the tag from an image reference, so a Deployment created
// by something other than this operator still reports a version.
func imageTag(image string) string {
	// A digest pins the image regardless of tag, so there is no version to
	// report -- and the digest's own colon must not be mistaken for a tag.
	if strings.Contains(image, "@") {
		return ""
	}
	// A registry may carry a port, whose colon comes before the last slash.
	slash := strings.LastIndex(image, "/")
	if colon := strings.LastIndex(image, ":"); colon > slash {
		return image[colon+1:]
	}
	return ""
}

func objectKeyStrings(keys []apply.ObjectKey) []string {
	if len(keys) == 0 {
		return nil
	}
	out := make([]string, 0, len(keys))
	for _, key := range keys {
		out = append(out, key.String())
	}
	return out
}

// fail records a failure on both the given condition and Degraded, and marks
// the resource as not ready.
func (r *AuthentikReconciler) fail(
	status *akv1alpha1.AuthentikStatus,
	ak *akv1alpha1.Authentik,
	conditionType, reason, message string,
) {
	status.Phase = akv1alpha1.PhaseFailed
	status.SetCondition(conditionType, string(metav1.ConditionFalse), reason, message, ak.Generation)
	status.SetCondition(akv1alpha1.ConditionDegraded, string(metav1.ConditionTrue), reason, message, ak.Generation)
	status.SetCondition(akv1alpha1.ConditionReady, string(metav1.ConditionFalse), reason, message, ak.Generation)
	// The operator has stopped working towards the desired state until
	// something changes, so it is no longer progressing.
	status.SetCondition(akv1alpha1.ConditionProgressing, string(metav1.ConditionFalse), reason, message, ak.Generation)
}

// event records a Kubernetes event, if a recorder is configured.
//
// The message is passed as an argument rather than as the format string, so an
// error containing a percent sign cannot be interpreted as a verb.
func (r *AuthentikReconciler) event(ak *akv1alpha1.Authentik, eventType, reason, action, message string) {
	if r.Recorder == nil {
		return
	}
	r.Recorder.Eventf(ak, nil, eventType, reason, action, "%s", message)
}

// patchStatus writes the status subresource, skipping the call when nothing
// changed.
func (r *AuthentikReconciler) patchStatus(
	ctx context.Context,
	ak *akv1alpha1.Authentik,
	status *akv1alpha1.AuthentikStatus,
) error {
	if equality.Semantic.DeepEqual(ak.Status, *status) {
		return nil
	}

	patch := client.MergeFrom(ak.DeepCopy())
	ak.Status = *status
	if err := r.Status().Patch(ctx, ak, patch); err != nil {
		return fmt.Errorf("failed to update Authentik status: %w", err)
	}
	return nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *AuthentikReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&akv1alpha1.Authentik{},
			// Reconciling writes status, and a status write is an update event
			// on this same resource. Without this filter the controller would
			// wake itself in a loop. Only spec changes, and deletion, bump the
			// generation.
			builder.WithPredicates(predicate.GenerationChangedPredicate{}),
		).
		// Migration Jobs are the operator's own objects, so a Job finishing
		// should wake the reconciler rather than waiting for the next poll.
		Owns(&batchv1.Job{}).
		// A Deployment being edited or deleted out from under the operator is
		// drift worth correcting promptly.
		Owns(&appsv1.Deployment{}).
		Named("authentik").
		Complete(r)
}
