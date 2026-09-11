// Package resources builds the Kubernetes objects that make up an authentik
// installation.
//
// These are ports of the authentik Helm chart's templates: object names, labels
// and selectors match what the chart produces, so an existing chart release is
// adopted rather than duplicated. The chart remains the reference for what is
// correct here; see lifecycle/charts/authentik.
package resources

import (
	"fmt"
	"maps"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	akv1alpha1 "goauthentik.io/lifecycle/operator/api/v1alpha1"
)

// The label keys and value live in the API package, next to OwnerSelector,
// because the pruner selects on exactly what these builders set.
const (
	ManagedByLabel     = akv1alpha1.ManagedByLabel
	InstanceOwnerLabel = akv1alpha1.InstanceOwnerLabel
	ManagedByValue     = akv1alpha1.ManagedByLabelValue
)

// Builder assembles the objects for one Authentik resource.
//
// Version is the resolved image tag rather than something read back off the
// spec, because with automatic updates enabled the operator decides it.
type Builder struct {
	Authentik *akv1alpha1.Authentik
	Version   string
}

func (b *Builder) Namespace() string {
	return b.Authentik.TargetNamespace()
}

// Labels go on every object. The last two are what the operator recognizes its
// own work by.
func (b *Builder) Labels(component string) map[string]string {
	labels := map[string]string{
		"app.kubernetes.io/part-of": akv1alpha1.DefaultName,
		"app.kubernetes.io/version": akv1alpha1.LabelSafeVersion(b.Version),
		ManagedByLabel:              ManagedByValue,
		InstanceOwnerLabel:          b.Authentik.OwnerLabelValue(),
	}
	maps.Copy(labels, b.SelectorLabels(component))

	if g := b.Authentik.Spec.Global; g != nil {
		maps.Copy(labels, g.AdditionalLabels)
	}
	return labels
}

// SelectorLabels identify a component's pods. They must stay stable across
// upgrades: a Deployment's selector is immutable, so changing these would make
// every existing Deployment un-updatable.
func (b *Builder) SelectorLabels(component string) map[string]string {
	labels := map[string]string{
		"app.kubernetes.io/name":     b.Authentik.BaseName(),
		"app.kubernetes.io/instance": b.Authentik.ReleaseName(),
	}
	if component != "" {
		labels["app.kubernetes.io/component"] = component
	}
	return labels
}

func (b *Builder) objectMeta(name, component string, extraLabels, annotations map[string]string) metav1.ObjectMeta {
	labels := b.Labels(component)
	maps.Copy(labels, extraLabels)

	return metav1.ObjectMeta{
		Name:        name,
		Namespace:   b.Namespace(),
		Labels:      labels,
		Annotations: nilIfEmpty(annotations),
	}
}

func (b *Builder) ServerName() string {
	return b.Authentik.ComponentFullname(b.Authentik.ServerComponentName())
}

func (b *Builder) WorkerName() string {
	return b.Authentik.ComponentFullname(b.Authentik.WorkerComponentName())
}

// ServiceAccountName is the ServiceAccount the worker uses to manage outposts.
func (b *Builder) ServiceAccountName() string {
	spec := b.Authentik.Spec.ServiceAccount

	override := ""
	if spec != nil {
		override = spec.FullnameOverride
	}
	if g := b.Authentik.Spec.Global; g != nil && g.FullnameOverride != "" {
		override = g.FullnameOverride
	}
	if override != "" {
		return akv1alpha1.TruncateName(override)
	}

	// The authentik-remote-cluster subchart pins fullnameOverride to
	// "authentik", so that is the fallback that applies in practice.
	return akv1alpha1.TruncateName(akv1alpha1.DefaultName)
}

// ClusterScopedName is the name for the cluster-scoped RBAC objects. It carries
// the namespace because ClusterRoles are global and two installs in different
// namespaces must not collide.
func (b *Builder) ClusterScopedName() string {
	return akv1alpha1.TruncateName(fmt.Sprintf("%s-%s", b.ServiceAccountName(), b.Namespace()))
}

// mergedMap layers maps left to right, returning nil when the result is empty
// so that objects do not carry an empty annotations block.
func mergedMap(sources ...map[string]string) map[string]string {
	merged := map[string]string{}
	for _, source := range sources {
		maps.Copy(merged, source)
	}
	return nilIfEmpty(merged)
}

func nilIfEmpty(m map[string]string) map[string]string {
	if len(m) == 0 {
		return nil
	}
	return m
}
