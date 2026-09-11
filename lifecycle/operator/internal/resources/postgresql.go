package resources

import (
	"cmp"
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/utils/ptr"

	akv1alpha1 "goauthentik.io/lifecycle/operator/api/v1alpha1"
)

// The bundled database is a single primary, which is what the chart's subchart
// defaults to as well. It exists so an evaluation install works out of the box;
// a production deployment should point authentik.postgresql at an external
// database that is backed up and upgraded separately.

const postgresqlComponent = "postgresql"

// postgresqlEnabled reports whether the operator runs the database.
func (b *Builder) postgresqlEnabled() bool {
	spec := b.Authentik.Spec.PostgreSQL
	return spec != nil && spec.Enabled != nil && *spec.Enabled
}

// PostgreSQLName is the name of the database's objects.
//
// Built from the release name rather than the chart fullname, because that is
// what both the chart's default authentik.postgresql.host and the Bitnami
// subchart's own naming produce. Using the fullname would move the database for
// any release whose name does not already contain "authentik".
func (b *Builder) PostgreSQLName() string {
	return akv1alpha1.TruncateName(fmt.Sprintf("%s-%s", b.Authentik.ReleaseName(), postgresqlComponent))
}

// PostgreSQLServiceName is the hostname authentik connects to. It matches the
// name the chart's subchart produces, so switching between them does not move
// the database.
func (b *Builder) PostgreSQLServiceName() string {
	return b.PostgreSQLName()
}

// postgresqlSpec returns the database configuration with absent sections filled
// in, so the builders below need no nil checks.
func (b *Builder) postgresqlSpec() *akv1alpha1.PostgreSQLSpec {
	spec := b.Authentik.Spec.PostgreSQL
	if spec == nil {
		spec = &akv1alpha1.PostgreSQLSpec{}
	}
	if spec.Auth == nil {
		spec.Auth = &akv1alpha1.PostgreSQLAuthSpec{}
	}
	if spec.Primary == nil {
		spec.Primary = &akv1alpha1.PostgreSQLPrimarySpec{}
	}
	return spec
}

// PostgreSQLSecret holds the generated database password, or nil when the
// database is off or the password comes from a Secret the user manages.
func (b *Builder) PostgreSQLSecret() *corev1.Secret {
	if !b.postgresqlEnabled() {
		return nil
	}
	spec := b.postgresqlSpec()
	if spec.Auth.ExistingSecret != "" || spec.Auth.Password == "" {
		return nil
	}

	return &corev1.Secret{
		ObjectMeta: b.objectMeta(b.PostgreSQLName(), postgresqlComponent, nil, nil),
		Type:       corev1.SecretTypeOpaque,
		Data:       map[string][]byte{defaultPostgresSecretKey: []byte(spec.Auth.Password)},
	}
}

// PostgreSQLService is the headless Service fronting the database.
func (b *Builder) PostgreSQLService() *corev1.Service {
	if !b.postgresqlEnabled() {
		return nil
	}

	return &corev1.Service{
		ObjectMeta: b.objectMeta(b.PostgreSQLName(), postgresqlComponent, nil, nil),
		Spec: corev1.ServiceSpec{
			// Headless: there is one primary, so a stable DNS name for the pod
			// is more useful than load balancing across it.
			ClusterIP: corev1.ClusterIPNone,
			Ports: []corev1.ServicePort{{
				Name:       postgresqlComponent,
				Protocol:   corev1.ProtocolTCP,
				Port:       defaultPostgresPort,
				TargetPort: intstr.FromString(postgresqlComponent),
			}},
			Selector: b.SelectorLabels(postgresqlComponent),
		},
	}
}

// PostgreSQLStatefulSet runs the database, or nil when it is off.
func (b *Builder) PostgreSQLStatefulSet() (*appsv1.StatefulSet, error) {
	if !b.postgresqlEnabled() {
		return nil, nil
	}
	spec := b.postgresqlSpec()

	passwordRef, err := b.postgresqlPasswordRef()
	if err != nil {
		return nil, err
	}

	database := cmp.Or(spec.Auth.Database, defaultPostgresDatabase)
	user := cmp.Or(spec.Auth.Username, defaultPostgresUser)

	env := []corev1.EnvVar{
		{Name: "POSTGRES_DB", Value: database},
		{Name: "POSTGRES_USER", Value: user},
		{Name: "POSTGRES_PASSWORD", ValueFrom: passwordRef},
		// The official image refuses to initialise into a non-empty directory,
		// and a PersistentVolume often arrives with a lost+found in it.
		{Name: "PGDATA", Value: postgresDataMount + "/" + postgresSubPath},
	}

	args := spec.Args
	if len(args) == 0 {
		args = []string{"-c", fmt.Sprintf("max_connections=%d",
			ptr.Deref(spec.MaxConnections, defaultPostgresMaxConnections))}
	}

	resources := corev1.ResourceRequirements{}
	if spec.Primary.Resources != nil {
		resources = *spec.Primary.Resources
	}

	container := corev1.Container{
		Name:            postgresqlComponent,
		Image:           b.postgresqlImage(spec),
		ImagePullPolicy: corev1.PullPolicy(defaultPullPolicy),
		Args:            args,
		Env:             env,
		Ports: []corev1.ContainerPort{{
			Name:          postgresqlComponent,
			ContainerPort: defaultPostgresPort,
			Protocol:      corev1.ProtocolTCP,
		}},
		VolumeMounts: []corev1.VolumeMount{{
			Name:      volumeNameData,
			MountPath: postgresDataMount,
		}},
		Resources:       resources,
		SecurityContext: spec.ContainerSecurityContext,
		// pg_isready reports the server is accepting connections, which is what
		// authentik waits for on startup.
		ReadinessProbe: postgresProbe(user, database, 5, 10),
		LivenessProbe:  postgresProbe(user, database, 30, 10),
	}

	statefulSet := &appsv1.StatefulSet{
		ObjectMeta: b.objectMeta(b.PostgreSQLName(), postgresqlComponent, nil, nil),
		Spec: appsv1.StatefulSetSpec{
			ServiceName: b.PostgreSQLName(),
			Replicas:    ptr.To(int32(1)),
			Selector:    &metav1.LabelSelector{MatchLabels: b.SelectorLabels(postgresqlComponent)},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{Labels: b.Labels(postgresqlComponent)},
				Spec: corev1.PodSpec{
					Containers:      []corev1.Container{container},
					SecurityContext: spec.PodSecurityContext,
					NodeSelector:    spec.Primary.NodeSelector,
					Tolerations:     spec.Primary.Tolerations,
				},
			},
		},
	}

	b.attachPostgreSQLStorage(statefulSet, spec)
	return statefulSet, nil
}

// attachPostgreSQLStorage gives the database either a persistent volume or, if
// persistence is turned off, an emptyDir.
func (b *Builder) attachPostgreSQLStorage(statefulSet *appsv1.StatefulSet, spec *akv1alpha1.PostgreSQLSpec) {
	persistence := spec.Primary.Persistence

	if persistence != nil && persistence.Enabled != nil && !*persistence.Enabled {
		// Explicitly opted out: the database lives and dies with the pod.
		statefulSet.Spec.Template.Spec.Volumes = []corev1.Volume{{
			Name:         volumeNameData,
			VolumeSource: corev1.VolumeSource{EmptyDir: &corev1.EmptyDirVolumeSource{}},
		}}
		return
	}

	if persistence != nil && persistence.ExistingClaim != "" {
		statefulSet.Spec.Template.Spec.Volumes = []corev1.Volume{{
			Name: volumeNameData,
			VolumeSource: corev1.VolumeSource{
				PersistentVolumeClaim: &corev1.PersistentVolumeClaimVolumeSource{
					ClaimName: persistence.ExistingClaim,
				},
			},
		}}
		return
	}

	size := defaultPostgresStorage
	var storageClass *string
	if persistence != nil {
		size = cmp.Or(persistence.Size, size)
		if persistence.StorageClass != "" {
			storageClass = ptr.To(persistence.StorageClass)
		}
	}

	statefulSet.Spec.VolumeClaimTemplates = []corev1.PersistentVolumeClaim{{
		ObjectMeta: metav1.ObjectMeta{Name: volumeNameData},
		Spec: corev1.PersistentVolumeClaimSpec{
			AccessModes:      []corev1.PersistentVolumeAccessMode{corev1.ReadWriteOnce},
			StorageClassName: storageClass,
			Resources: corev1.VolumeResourceRequirements{
				Requests: corev1.ResourceList{corev1.ResourceStorage: resource.MustParse(size)},
			},
		},
	}}
}

// postgresqlPasswordRef points at the Secret key holding the password.
func (b *Builder) postgresqlPasswordRef() (*corev1.EnvVarSource, error) {
	spec := b.postgresqlSpec()

	if spec.Auth.ExistingSecret != "" {
		return secretKeyRef(spec.Auth.ExistingSecret,
			cmp.Or(spec.Auth.SecretKey, defaultPostgresSecretKey)), nil
	}
	if spec.Auth.Password == "" {
		return nil, fmt.Errorf("postgresql.auth.password or postgresql.auth.existingSecret is required when postgresql is enabled")
	}
	return secretKeyRef(b.PostgreSQLName(), defaultPostgresSecretKey), nil
}

// postgresqlImage assembles the database image reference.
func (b *Builder) postgresqlImage(spec *akv1alpha1.PostgreSQLSpec) string {
	registry, repository, tag := defaultPostgresRegistry, defaultPostgresRepository, defaultPostgresTag
	if spec.Image != nil {
		registry = cmp.Or(spec.Image.Registry, registry)
		repository = cmp.Or(spec.Image.Repository, repository)
		tag = cmp.Or(spec.Image.Tag, tag)
	}
	return fmt.Sprintf("%s/%s:%s", registry, repository, tag)
}

func postgresProbe(user, database string, initialDelay, period int32) *corev1.Probe {
	return &corev1.Probe{
		ProbeHandler: corev1.ProbeHandler{
			Exec: &corev1.ExecAction{
				Command: []string{"pg_isready", "-U", user, "-d", database},
			},
		},
		InitialDelaySeconds: initialDelay,
		PeriodSeconds:       period,
		TimeoutSeconds:      5,
		FailureThreshold:    6,
	}
}
