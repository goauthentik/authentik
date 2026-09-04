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

package resources

import (
	corev1 "k8s.io/api/core/v1"
	rbacv1 "k8s.io/api/rbac/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// outpostVerbs are the verbs the worker needs on the objects it creates for a
// Kubernetes outpost. A port of the chart's authentik-remote-cluster.api-verbs-rw.
var outpostVerbs = []string{"get", "create", "delete", "list", "patch"}

// serviceAccountEnabled reports whether the operator manages the ServiceAccount
// and RBAC the worker uses to deploy outposts into this cluster.
func (b *Builder) serviceAccountEnabled() bool {
	spec := b.Authentik.Spec.ServiceAccount
	if spec == nil || spec.Create == nil {
		// The chart defaults this on, because a Kubernetes outpost is the
		// common case and it cannot work without these permissions.
		return true
	}
	return *spec.Create
}

// serviceAccountAnnotations are applied to every object in this group, which is
// how the chart lets a cloud IAM role be bound to the ServiceAccount.
func (b *Builder) serviceAccountAnnotations() map[string]string {
	if spec := b.Authentik.Spec.ServiceAccount; spec != nil {
		return spec.Annotations
	}
	return nil
}

// ServiceAccount is the identity the worker runs as, or nil when disabled.
func (b *Builder) ServiceAccount() *corev1.ServiceAccount {
	if !b.serviceAccountEnabled() {
		return nil
	}

	return &corev1.ServiceAccount{
		ObjectMeta: b.objectMeta(b.ServiceAccountName(), "", nil, b.serviceAccountAnnotations()),
	}
}

// ServiceAccountTokenSecret is a long-lived token for the ServiceAccount, or
// nil when not requested.
//
// Kubernetes stopped minting these automatically in 1.24. authentik needs one
// only when something outside the cluster uses the credentials; in-cluster the
// projected token the kubelet mounts is enough.
func (b *Builder) ServiceAccountTokenSecret() *corev1.Secret {
	spec := b.Authentik.Spec.ServiceAccount
	if !b.serviceAccountEnabled() || spec == nil ||
		spec.ServiceAccountSecret == nil || !spec.ServiceAccountSecret.Enabled {
		return nil
	}

	name := b.ServiceAccountName()
	annotations := mergedMap(
		map[string]string{corev1.ServiceAccountNameKey: name},
		b.serviceAccountAnnotations(),
	)

	return &corev1.Secret{
		ObjectMeta: b.objectMeta(name, "", nil, annotations),
		Type:       corev1.SecretTypeServiceAccountToken,
	}
}

// Role grants the worker what it needs to manage outposts in this namespace.
func (b *Builder) Role() *rbacv1.Role {
	if !b.serviceAccountEnabled() {
		return nil
	}

	return &rbacv1.Role{
		ObjectMeta: b.objectMeta(b.ServiceAccountName(), "", nil, b.serviceAccountAnnotations()),
		Rules: []rbacv1.PolicyRule{
			{
				APIGroups: []string{""},
				Resources: []string{"secrets", "services", "configmaps"},
				Verbs:     outpostVerbs,
			},
			{
				APIGroups: []string{"extensions", "apps"},
				Resources: []string{"deployments"},
				Verbs:     outpostVerbs,
			},
			{
				APIGroups: []string{"extensions", "networking.k8s.io"},
				Resources: []string{"ingresses"},
				Verbs:     outpostVerbs,
			},
			{
				APIGroups: []string{"traefik.containo.us", "traefik.io"},
				Resources: []string{"middlewares"},
				Verbs:     outpostVerbs,
			},
			{
				APIGroups: []string{"gateway.networking.k8s.io"},
				Resources: []string{"httproutes"},
				Verbs:     outpostVerbs,
			},
			{
				APIGroups: []string{"monitoring.coreos.com"},
				Resources: []string{"servicemonitors"},
				Verbs:     outpostVerbs,
			},
			{
				// Read-only, so the worker can tell which optional CRDs exist
				// before trying to create the objects that need them.
				APIGroups: []string{"apiextensions.k8s.io"},
				Resources: []string{"customresourcedefinitions"},
				Verbs:     []string{verbList},
			},
		},
	}
}

// RoleBinding binds the Role to the ServiceAccount.
func (b *Builder) RoleBinding() *rbacv1.RoleBinding {
	if !b.serviceAccountEnabled() {
		return nil
	}

	name := b.ServiceAccountName()
	return &rbacv1.RoleBinding{
		ObjectMeta: b.objectMeta(name, "", nil, b.serviceAccountAnnotations()),
		RoleRef: rbacv1.RoleRef{
			APIGroup: rbacv1.GroupName,
			Kind:     "Role",
			Name:     name,
		},
		Subjects: []rbacv1.Subject{{
			Kind:      rbacv1.ServiceAccountKind,
			Name:      name,
			Namespace: b.Namespace(),
		}},
	}
}

// ClusterRole lets the worker list CRDs, which is cluster-scoped and so cannot
// be granted by a Role.
func (b *Builder) ClusterRole() *rbacv1.ClusterRole {
	if !b.clusterRoleEnabled() {
		return nil
	}

	role := &rbacv1.ClusterRole{
		ObjectMeta: b.objectMeta(b.ClusterScopedName(), "", nil, b.serviceAccountAnnotations()),
		Rules: []rbacv1.PolicyRule{{
			APIGroups: []string{"apiextensions.k8s.io"},
			Resources: []string{"customresourcedefinitions"},
			Verbs:     []string{verbList},
		}},
	}
	// Cluster-scoped objects have no namespace, and setting one makes the API
	// server reject the apply.
	role.Namespace = ""
	return role
}

// ClusterRoleBinding binds the ClusterRole to the ServiceAccount.
func (b *Builder) ClusterRoleBinding() *rbacv1.ClusterRoleBinding {
	if !b.clusterRoleEnabled() {
		return nil
	}

	name := b.ClusterScopedName()
	binding := &rbacv1.ClusterRoleBinding{
		ObjectMeta: b.objectMeta(name, "", nil, b.serviceAccountAnnotations()),
		RoleRef: rbacv1.RoleRef{
			APIGroup: rbacv1.GroupName,
			Kind:     "ClusterRole",
			Name:     name,
		},
		Subjects: []rbacv1.Subject{{
			Kind:      rbacv1.ServiceAccountKind,
			Name:      b.ServiceAccountName(),
			Namespace: b.Namespace(),
		}},
	}
	binding.Namespace = ""
	return binding
}

// clusterRoleEnabled reports whether the cluster-scoped RBAC is wanted. The
// chart's subchart defaults it on alongside the ServiceAccount.
func (b *Builder) clusterRoleEnabled() bool {
	return b.serviceAccountEnabled()
}

// ClusterScopedObjects lists the cluster-scoped objects this instance owns.
//
// Owner references cannot span from a namespaced resource to a cluster-scoped
// one, so these are not garbage collected with the Authentik resource and have
// to be deleted explicitly when it goes away.
func (b *Builder) ClusterScopedObjects() []metav1.Object {
	objects := []metav1.Object{}
	if role := b.ClusterRole(); role != nil {
		objects = append(objects, role)
	}
	if binding := b.ClusterRoleBinding(); binding != nil {
		objects = append(objects, binding)
	}
	return objects
}
