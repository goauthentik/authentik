package resources

import (
	corev1 "k8s.io/api/core/v1"
	rbacv1 "k8s.io/api/rbac/v1"
)

// outpostVerbs are the verbs the worker needs on the objects it creates for a
// Kubernetes outpost.
var outpostVerbs = []string{"get", "create", "delete", "list", "patch"}

// serviceAccountEnabled reports whether the operator manages the ServiceAccount
// and RBAC the worker uses to deploy outposts into this cluster.
func (b *Builder) serviceAccountEnabled() bool {
	spec := b.Authentik.Spec.ServiceAccount
	if spec == nil || spec.Create == nil {
		// Defaults on: a Kubernetes outpost is the common case and cannot
		// work without these permissions.
		return true
	}
	return *spec.Create
}

// serviceAccountAnnotations go on every object in this group, which is how a
// cloud IAM role is bound to the ServiceAccount.
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
				Verbs:     []string{"list"},
			},
		},
	}
}

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
	if !b.serviceAccountEnabled() {
		return nil
	}

	role := &rbacv1.ClusterRole{
		ObjectMeta: b.objectMeta(b.ClusterScopedName(), "", nil, b.serviceAccountAnnotations()),
		Rules: []rbacv1.PolicyRule{{
			APIGroups: []string{"apiextensions.k8s.io"},
			Resources: []string{"customresourcedefinitions"},
			Verbs:     []string{"list"},
		}},
	}
	// Cluster-scoped objects have no namespace, and setting one makes the API
	// server reject the apply.
	role.Namespace = ""
	return role
}

func (b *Builder) ClusterRoleBinding() *rbacv1.ClusterRoleBinding {
	if !b.serviceAccountEnabled() {
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
