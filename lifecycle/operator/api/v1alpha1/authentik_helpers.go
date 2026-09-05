package v1alpha1

import (
	"cmp"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"regexp"
	"strings"
	"time"

	"k8s.io/apimachinery/pkg/api/meta"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// DefaultChartName is the chart name the naming templates fall back to. It has
// to match the name in the chart's Chart.yaml.
const DefaultChartName = "authentik"

// Operator-only defaults.
const (
	// DefaultReconcileInterval is how often the desired state is re-applied
	// when nothing has changed, to correct drift.
	DefaultReconcileInterval = 5 * time.Minute

	// DefaultAutoUpdateInterval is how often the registry is polled for new
	// builds of the tracked branch.
	DefaultAutoUpdateInterval = 5 * time.Minute
)

// Migration Job defaults.
const (
	// DefaultMigrationBackoffLimit is how many times the migration Job retries.
	DefaultMigrationBackoffLimit int32 = 3

	// DefaultMigrationDeadlineSeconds fails a migration that runs too long.
	DefaultMigrationDeadlineSeconds int64 = 3600

	// DefaultMigrationTTLSeconds keeps a finished migration Job around for a
	// day so its logs can still be read.
	DefaultMigrationTTLSeconds int32 = 86400
)

// MigrateCommand is authentik's migrate subcommand, also used as the migration
// component name.
const MigrateCommand = "migrate"

// DefaultMigrationCommand runs authentik's system migrations followed by the
// Django ones. `ak` waits for the database to accept connections first.
var DefaultMigrationCommand = []string{"ak", MigrateCommand}

// DefaultImageRepository is the image the chart deploys by default.
const DefaultImageRepository = "ghcr.io/goauthentik/server"

// ReleaseName prefixes the objects belonging to this instance.
func (a *Authentik) ReleaseName() string {
	if a.Spec.ReleaseName != "" {
		return a.Spec.ReleaseName
	}
	return a.Name
}

// TargetNamespace is the namespace the chart's objects are deployed into.
func (a *Authentik) TargetNamespace() string {
	if g := a.Spec.Global; g != nil && g.NamespaceOverride != "" {
		return g.NamespaceOverride
	}
	return a.Namespace
}

// ChartObjectName mirrors the chart's "authentik.name" template: the base name
// the chart's object names are built from.
func (a *Authentik) ChartObjectName() string {
	name := DefaultChartName
	if a.Spec.NameOverride != "" {
		name = a.Spec.NameOverride
	}
	if g := a.Spec.Global; g != nil && g.NameOverride != "" {
		name = g.NameOverride
	}
	return TruncateName(name)
}

// Fullname mirrors the chart's "authentik.fullname" template: the prefix shared
// by the objects the chart creates.
func (a *Authentik) Fullname() string {
	fullnameOverride := a.Spec.FullnameOverride
	if g := a.Spec.Global; g != nil && g.FullnameOverride != "" {
		fullnameOverride = g.FullnameOverride
	}
	if fullnameOverride != "" {
		return TruncateName(fullnameOverride)
	}

	name := a.ChartObjectName()
	release := a.ReleaseName()
	if strings.Contains(release, name) {
		return TruncateName(release)
	}
	return TruncateName(fmt.Sprintf("%s-%s", release, name))
}

// ComponentFullname is the name of the objects belonging to one component,
// mirroring the chart's "authentik.server.fullname" and
// "authentik.worker.fullname" templates.
func (a *Authentik) ComponentFullname(component string) string {
	return TruncateName(fmt.Sprintf("%s-%s", a.Fullname(), component))
}

// ServerComponentName is the server's component name, which the chart uses as
// an object name suffix and as the app.kubernetes.io/component label.
func (a *Authentik) ServerComponentName() string {
	if s := a.Spec.Server; s != nil && s.Name != "" {
		return s.Name
	}
	return "server"
}

// WorkerComponentName is the worker's component name.
func (a *Authentik) WorkerComponentName() string {
	if w := a.Spec.Worker; w != nil && w.Name != "" {
		return w.Name
	}
	return "worker"
}

// ConfigSecretName is the Secret holding the authentik configuration that the
// containers read their environment from.
func (a *Authentik) ConfigSecretName() string {
	if c := a.Spec.Authentik; c != nil && c.ExistingSecret != nil && c.ExistingSecret.SecretName != "" {
		return c.ExistingSecret.SecretName
	}
	return a.Fullname()
}

// TruncateName applies the 63-character DNS label limit the chart's naming
// templates enforce.
func TruncateName(name string) string {
	if len(name) > 63 {
		name = name[:63]
	}
	return strings.TrimSuffix(name, "-")
}

// unsafeLabelChars matches everything a label value may not contain.
var unsafeLabelChars = regexp.MustCompile(`[^a-zA-Z0-9._-]`)

// LabelSafeVersion makes an image tag usable as a label value, matching the
// chart's authentik.versionLabelValue helper: at most 63 characters of
// alphanumerics, dashes, underscores and dots, with alphanumeric ends.
func LabelSafeVersion(version string) string {
	return strings.Trim(TruncateName(unsafeLabelChars.ReplaceAllString(version, "-")), "-_.")
}

// ImageRepository is the repository the authentik server and worker images come
// from.
func (a *Authentik) ImageRepository() string {
	if g := a.Spec.Global; g != nil && g.Image != nil && g.Image.Repository != "" {
		return g.Image.Repository
	}
	return DefaultImageRepository
}

// ImageDigest is the digest the authentik image is pinned to, if any. A digest
// pins the image regardless of tag, so version tracking is meaningless while
// one is set.
func (a *Authentik) ImageDigest() string {
	if g := a.Spec.Global; g != nil && g.Image != nil {
		return g.Image.Digest
	}
	return ""
}

// ImageRef builds the full image reference for a tag, matching how the chart's
// Deployment templates assemble it.
func (a *Authentik) ImageRef(tag string) string {
	ref := fmt.Sprintf("%s:%s", a.ImageRepository(), tag)
	if digest := a.ImageDigest(); digest != "" {
		ref = fmt.Sprintf("%s@%s", ref, digest)
	}
	return ref
}

// AutoUpdateEnabled reports whether the operator manages the image tag.
func (a *Authentik) AutoUpdateEnabled() bool {
	return a.Spec.AutoUpdate != nil && a.Spec.AutoUpdate.Enabled && a.Spec.AutoUpdate.Branch != ""
}

// AutoUpdateRepository is the repository to look for branch tags in.
func (a *Authentik) AutoUpdateRepository() string {
	if au := a.Spec.AutoUpdate; au != nil && au.Repository != "" {
		return au.Repository
	}
	return a.ImageRepository()
}

// AutoUpdateTagStrategy is how the tracked branch is turned into a tag.
func (a *Authentik) AutoUpdateTagStrategy() TagStrategy {
	if au := a.Spec.AutoUpdate; au != nil && au.TagStrategy != "" {
		return au.TagStrategy
	}
	return TagStrategyImmutable
}

// AutoUpdateInterval is how often the registry is polled.
func (a *Authentik) AutoUpdateInterval() time.Duration {
	if au := a.Spec.AutoUpdate; au != nil && au.Interval != nil && au.Interval.Duration > 0 {
		return au.Interval.Duration
	}
	return DefaultAutoUpdateInterval
}

// ConfiguredTag is the image tag set in the spec, if any. Empty means the chart
// falls back to its own appVersion.
func (a *Authentik) ConfiguredTag() string {
	if g := a.Spec.Global; g != nil && g.Image != nil {
		return g.Image.Tag
	}
	return ""
}

// ReconcileInterval is how often the desired state is re-applied.
func (a *Authentik) ReconcileInterval() time.Duration {
	if a.Spec.ReconcileInterval != nil && a.Spec.ReconcileInterval.Duration > 0 {
		return a.Spec.ReconcileInterval.Duration
	}
	return DefaultReconcileInterval
}

// PruneEnabled reports whether objects that dropped out of the desired state
// are deleted.
func (a *Authentik) PruneEnabled() bool {
	if a.Spec.Prune != nil {
		return *a.Spec.Prune
	}
	return true
}

// OwnerLabelValue identifies this resource. The resource's own namespace is
// included because namespaceOverride lets objects live somewhere else.
func (a *Authentik) OwnerLabelValue() string {
	return fmt.Sprintf("%s.%s", a.Name, a.Namespace)
}

// OwnerSelector selects the objects this resource owns, and is what bounds
// pruning to the operator's own work.
func (a *Authentik) OwnerSelector() map[string]string {
	return map[string]string{
		ManagedByLabel:     ManagedByLabelValue,
		InstanceOwnerLabel: a.OwnerLabelValue(),
	}
}

// MigrationsEnabled reports whether upgrades are gated behind a migration Job.
func (a *Authentik) MigrationsEnabled() bool {
	if m := a.Spec.Migrations; m != nil && m.Enabled != nil {
		return *m.Enabled
	}
	return true
}

// MigrationCommand is the command the migration Job runs.
func (a *Authentik) MigrationCommand() []string {
	if m := a.Spec.Migrations; m != nil && len(m.Command) > 0 {
		return m.Command
	}
	return DefaultMigrationCommand
}

// Labels the operator sets on everything it creates. OwnerSelector selects on
// them, so the builders and the pruner have to agree; they are defined here
// once for that reason.
const (
	// ManagedByLabel marks an object as belonging to this operator.
	ManagedByLabel = "app.kubernetes.io/managed-by"

	// InstanceOwnerLabel identifies which Authentik resource an object belongs
	// to. Two instances in one namespace would otherwise prune each other's
	// objects, since owner references are not selectable.
	InstanceOwnerLabel = "instance.goauthentik.io/owner"

	// ManagedByLabelValue is the value of ManagedByLabel.
	//
	// The chart sets app.kubernetes.io/managed-by to "Helm". A distinct value
	// keeps the pruning selector from ever matching a Helm-managed object, so a
	// misconfigured operator cannot delete another tool's resources.
	ManagedByLabelValue = "authentik-operator"
)

// SetCondition adds or updates a condition, leaving LastTransitionTime alone
// when only the message changed.
func (s *AuthentikStatus) SetCondition(conditionType, status, reason, message string, generation int64) {
	meta.SetStatusCondition(&s.Conditions, metav1.Condition{
		Type:               conditionType,
		Status:             metav1.ConditionStatus(status),
		Reason:             reason,
		Message:            message,
		ObservedGeneration: generation,
	})
}

// DesiredStateHash fingerprints what decides the deployed result: the spec and
// the resolved version. Reconciliation compares it against the hash recorded on
// the cluster to tell a genuine change from a periodic re-reconcile.
func DesiredStateHash(spec *AuthentikSpec, targetVersion string) (string, error) {
	// json.Marshal sorts map keys, so equivalent specs always hash the same.
	encoded, err := json.Marshal(struct {
		Version string         `json:"version"`
		Spec    *AuthentikSpec `json:"spec"`
	}{Version: targetVersion, Spec: spec})
	if err != nil {
		return "", fmt.Errorf("failed to hash the desired state: %w", err)
	}

	digest := sha256.Sum256(encoded)
	return hex.EncodeToString(digest[:]), nil
}

// GetAffinity returns the affinity preset, filling in the defaults the chart's
// values.yaml supplies: replicas prefer separate nodes, and node affinity is
// only applied when match expressions are actually given.
func (g *GlobalSpec) GetAffinity() AffinityPreset {
	preset := AffinityPreset{
		PodAntiAffinity: "soft",
		NodeAffinity:    &NodeAffinityPreset{Type: "hard"},
	}
	if g == nil || g.Affinity == nil {
		return preset
	}

	if g.Affinity.PodAntiAffinity != "" {
		preset.PodAntiAffinity = g.Affinity.PodAntiAffinity
	}
	if node := g.Affinity.NodeAffinity; node != nil {
		preset.NodeAffinity = &NodeAffinityPreset{
			Type:             cmp.Or(node.Type, preset.NodeAffinity.Type),
			MatchExpressions: node.MatchExpressions,
		}
	}
	return preset
}
