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

// Package resources builds the Kubernetes objects that make up an authentik
// installation.
//
// These are ports of the authentik Helm chart's templates. Object names, labels
// and selectors match what the chart produces, so an existing chart release can
// be adopted by the operator without recreating anything. The chart remains the
// reference for what is correct here; see lifecycle/charts/authentik.
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

// Namespace is where the built objects belong.
func (b *Builder) Namespace() string {
	return b.Authentik.TargetNamespace()
}

// Labels are the common labels the chart puts on every object, plus the two the
// operator needs to recognize its own work.
func (b *Builder) Labels(component string) map[string]string {
	labels := map[string]string{
		"app.kubernetes.io/part-of": "authentik",
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
		"app.kubernetes.io/name":     b.Authentik.ChartObjectName(),
		"app.kubernetes.io/instance": b.Authentik.ReleaseName(),
	}
	if component != "" {
		labels["app.kubernetes.io/component"] = component
	}
	return labels
}

// objectMeta is the metadata shared by every built object.
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

// ServerName is the name of the server's objects.
func (b *Builder) ServerName() string {
	return b.Authentik.ComponentFullname(b.Authentik.ServerComponentName())
}

// WorkerName is the name of the worker's objects.
func (b *Builder) WorkerName() string {
	return b.Authentik.ComponentFullname(b.Authentik.WorkerComponentName())
}

// ServiceAccountName is the name of the ServiceAccount the worker uses to
// manage outposts, mirroring the authentik-remote-cluster chart's fullname.
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

	// The subchart's own name is "authentik-remote-cluster", but the parent
	// chart pins fullnameOverride to "authentik", so this is the fallback that
	// actually applies in practice.
	return akv1alpha1.TruncateName(akv1alpha1.DefaultChartName)
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
