package v1alpha1

import (
	corev1 "k8s.io/api/core/v1"
	apiextensionsv1 "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
)

// AuthentikExistingSecret reads the whole authentik configuration from a Secret
// that already exists, instead of having the operator render one.
type AuthentikExistingSecret struct {
	// secretName is the name of the Secret to use. Its keys must be authentik
	// configuration option names, see
	// https://docs.goauthentik.io/install-config/configuration/.
	// When set, every other field under authentik is ignored.
	// +optional
	SecretName string `json:"secretName,omitempty"`
}

// AuthentikContextProcessors configures the paths authentik reads the GeoIP
// databases from. GeoIP features stay disabled if the files are absent.
type AuthentikContextProcessors struct {
	// geoip is the path to the GeoIP City database.
	// +optional
	GeoIP string `json:"geoip,omitempty"`

	// asn is the path to the GeoIP ASN database.
	// +optional
	ASN string `json:"asn,omitempty"`
}

// AuthentikEventsConfig configures authentik's event pipeline.
type AuthentikEventsConfig struct {
	// context_processors enriches events with extra context.
	// +optional
	ContextProcessors *AuthentikContextProcessors `json:"context_processors,omitempty"`
}

// AuthentikWebConfig configures how authentik is served.
type AuthentikWebConfig struct {
	// path is the relative path authentik is served under. Must have both a
	// leading and a trailing slash.
	// +kubebuilder:validation:Pattern=`^/.*/$`
	// +optional
	Path string `json:"path,omitempty"`
}

// AuthentikEmailConfig configures the SMTP server authentik sends mail through.
type AuthentikEmailConfig struct {
	// host is the SMTP server hostname. Leave empty to disable email.
	// +optional
	Host string `json:"host,omitempty"`

	// port is the SMTP server port.
	// +optional
	Port *int32 `json:"port,omitempty"`

	// username is the SMTP username. Leave empty for no authentication.
	// +optional
	Username string `json:"username,omitempty"`

	// password is the SMTP password. Leave empty for no authentication.
	// Consider authentik.existingSecret instead of putting this in the spec.
	// +optional
	Password string `json:"password,omitempty"`

	// use_tls enables StartTLS. Mutually exclusive with use_ssl.
	// +optional
	UseTLS *bool `json:"use_tls,omitempty"`

	// use_ssl enables implicit TLS. Mutually exclusive with use_tls.
	// +optional
	UseSSL *bool `json:"use_ssl,omitempty"`

	// timeout is the connection timeout in seconds.
	// +optional
	Timeout *int32 `json:"timeout,omitempty"`

	// from is the sender address, either "foo@bar.baz" or
	// "authentik <foo@bar.baz>".
	// +optional
	From string `json:"from,omitempty"`
}

// AuthentikOutpostsConfig configures how managed outposts are deployed.
type AuthentikOutpostsConfig struct {
	// container_image_base is the image template used for managed outposts.
	// Supports the %(type)s, %(version)s and %(build_hash)s placeholders.
	// +optional
	ContainerImageBase string `json:"container_image_base,omitempty"`
}

// AuthentikErrorReportingConfig configures opt-in error reporting.
type AuthentikErrorReportingConfig struct {
	// enabled opts in to sending anonymous usage data, stack traces and
	// performance data.
	// +optional
	Enabled *bool `json:"enabled,omitempty"`

	// environment is the environment name attached to error reports.
	// +optional
	Environment string `json:"environment,omitempty"`

	// send_pii includes personally identifiable information in error reports.
	// +optional
	SendPII *bool `json:"send_pii,omitempty"`
}

// AuthentikPostgreSQLConfig tells authentik which database to connect to. This
// is separate from the postgresql field, which decides whether the operator
// deploys that database.
type AuthentikPostgreSQLConfig struct {
	// host is the PostgreSQL hostname. Defaults to the bundled database.
	// +optional
	Host string `json:"host,omitempty"`

	// name is the database name.
	// +optional
	Name string `json:"name,omitempty"`

	// user is the database user.
	// +optional
	User string `json:"user,omitempty"`

	// password is the database password. Consider authentik.existingSecret
	// instead of putting this in the spec.
	// +optional
	Password string `json:"password,omitempty"`

	// port is the database port.
	// +optional
	Port *int32 `json:"port,omitempty"`
}

// AuthentikConfigSpec is the authentik application configuration. It is
// rendered into a Secret and injected into every authentik container as
// AUTHENTIK_-prefixed environment variables.
//
// The commonly used options are typed here; anything else authentik accepts can
// go into extraConfig. See
// https://docs.goauthentik.io/install-config/configuration/ for the full list.
type AuthentikConfigSpec struct {
	// enabled renders the authentik configuration Secret. Defaults to true.
	// +optional
	Enabled *bool `json:"enabled,omitempty"`

	// log_level is the log level for the server and worker.
	// +kubebuilder:validation:Enum=trace;debug;info;warning;error
	// +optional
	LogLevel string `json:"log_level,omitempty"`

	// secret_key signs cookies and derives unique user IDs. Generate a random
	// value and never change it after the first install. Consider
	// authentik.existingSecret instead of putting this in the spec.
	// +optional
	SecretKey string `json:"secret_key,omitempty"`

	// existingSecret reads the whole configuration from an existing Secret.
	// +optional
	ExistingSecret *AuthentikExistingSecret `json:"existingSecret,omitempty"`

	// events configures the event pipeline.
	// +optional
	Events *AuthentikEventsConfig `json:"events,omitempty"`

	// web configures how authentik is served.
	// +optional
	Web *AuthentikWebConfig `json:"web,omitempty"`

	// email configures the outgoing SMTP server.
	// +optional
	Email *AuthentikEmailConfig `json:"email,omitempty"`

	// outposts configures managed outpost deployment.
	// +optional
	Outposts *AuthentikOutpostsConfig `json:"outposts,omitempty"`

	// error_reporting configures opt-in error reporting.
	// +optional
	ErrorReporting *AuthentikErrorReportingConfig `json:"error_reporting,omitempty"`

	// postgresql tells authentik which database to connect to.
	// +optional
	PostgreSQL *AuthentikPostgreSQLConfig `json:"postgresql,omitempty"`

	// extraConfig holds any other authentik configuration option, nested the
	// same way as the typed fields above. Nested keys are joined with a double
	// underscore, so {"cache": {"timeout": 600}} becomes
	// AUTHENTIK_CACHE__TIMEOUT=600.
	// +optional
	ExtraConfig *apiextensionsv1.JSON `json:"extraConfig,omitempty"`
}

// PostgreSQLAuthSpec configures credentials for the bundled database.
type PostgreSQLAuthSpec struct {
	// username is the application database user to create.
	// +optional
	Username string `json:"username,omitempty"`

	// database is the database to create.
	// +optional
	Database string `json:"database,omitempty"`

	// password is the password for username. Prefer existingSecret.
	// +optional
	Password string `json:"password,omitempty"`

	// existingSecret reads the passwords from an existing Secret.
	// +optional
	ExistingSecret string `json:"existingSecret,omitempty"`

	// secretKey is the key within existingSecret holding the password for
	// username. Defaults to "password".
	// +optional
	SecretKey string `json:"secretKey,omitempty"`
}

// PostgreSQLPersistenceSpec configures the bundled database's storage.
type PostgreSQLPersistenceSpec struct {
	// enabled provisions a PersistentVolumeClaim. Disabling it means the
	// database lives in an emptyDir and is lost when the pod is replaced.
	// +optional
	Enabled *bool `json:"enabled,omitempty"`

	// storageClass is the StorageClass to provision from.
	// +optional
	StorageClass string `json:"storageClass,omitempty"`

	// size is the volume size, e.g. 8Gi.
	// +optional
	Size string `json:"size,omitempty"`

	// existingClaim uses an existing PersistentVolumeClaim.
	// +optional
	ExistingClaim string `json:"existingClaim,omitempty"`
}

// PostgreSQLPrimarySpec configures the bundled database's primary instance.
type PostgreSQLPrimarySpec struct {
	// persistence configures the primary's storage.
	// +optional
	Persistence *PostgreSQLPersistenceSpec `json:"persistence,omitempty"`

	// resources are the primary's resource requests and limits.
	// +optional
	Resources *corev1.ResourceRequirements `json:"resources,omitempty"`

	// nodeSelector schedules the primary onto matching nodes.
	// +optional
	NodeSelector map[string]string `json:"nodeSelector,omitempty"`

	// tolerations let the primary schedule onto tainted nodes.
	// +optional
	Tolerations []corev1.Toleration `json:"tolerations,omitempty"`
}

// PostgreSQLImageSpec selects the image for the bundled database.
type PostgreSQLImageSpec struct {
	// registry is the image registry.
	// +optional
	Registry string `json:"registry,omitempty"`

	// repository is the image repository.
	// +optional
	Repository string `json:"repository,omitempty"`

	// tag is the image tag.
	// +optional
	Tag string `json:"tag,omitempty"`
}

// PostgreSQLSpec configures the PostgreSQL database bundled with authentik.
//
// This is off by default: it is convenient for evaluation, but an external,
// separately backed-up PostgreSQL is the recommended setup. Point
// authentik.postgresql at it and leave this disabled.
type PostgreSQLSpec struct {
	// enabled deploys a PostgreSQL StatefulSet alongside authentik.
	// +optional
	Enabled *bool `json:"enabled,omitempty"`

	// image selects the PostgreSQL image.
	// +optional
	Image *PostgreSQLImageSpec `json:"image,omitempty"`

	// auth configures the database credentials.
	// +optional
	Auth *PostgreSQLAuthSpec `json:"auth,omitempty"`

	// primary configures the primary instance.
	// +optional
	Primary *PostgreSQLPrimarySpec `json:"primary,omitempty"`

	// maxConnections is the server's max_connections setting. authentik opens a
	// connection per worker thread, so the Postgres default of 100 is too low
	// for more than a couple of replicas.
	// +kubebuilder:validation:Minimum=1
	// +optional
	MaxConnections *int32 `json:"maxConnections,omitempty"`

	// args overrides the arguments passed to the postgres binary. Setting this
	// replaces the arguments the operator would otherwise derive, including
	// maxConnections.
	// +optional
	Args []string `json:"args,omitempty"`

	// podSecurityContext is the database pod's security context.
	// +optional
	PodSecurityContext *corev1.PodSecurityContext `json:"podSecurityContext,omitempty"`

	// containerSecurityContext is the database container's security context.
	// +optional
	ContainerSecurityContext *corev1.SecurityContext `json:"containerSecurityContext,omitempty"`
}

// MigrationsSpec controls the database migration Job the operator runs before
// it rolls a new authentik version out to the server and worker Deployments.
//
// Without this gate, a rolling update starts new pods that migrate the database
// while old pods are still serving against the old schema. Running migrations
// once, to completion, in a Job first keeps that window closed.
//
// The gate only applies to upgrades. A first install has nothing to migrate
// away from, so the Deployments are created directly.
type MigrationsSpec struct {
	// enabled runs migrations in a Job and blocks the upgrade until it
	// succeeds. Defaults to true.
	// +optional
	Enabled *bool `json:"enabled,omitempty"`

	// command is the migration command. Defaults to ["ak", "migrate"].
	// +optional
	Command []string `json:"command,omitempty"`

	// backoffLimit is how many times the Job retries before the upgrade is
	// reported as failed. Defaults to 3.
	// +kubebuilder:validation:Minimum=0
	// +optional
	BackoffLimit *int32 `json:"backoffLimit,omitempty"`

	// activeDeadlineSeconds fails the migration Job if it runs longer than
	// this. Defaults to 3600.
	// +kubebuilder:validation:Minimum=1
	// +optional
	ActiveDeadlineSeconds *int64 `json:"activeDeadlineSeconds,omitempty"`

	// ttlSecondsAfterFinished is how long a finished migration Job is kept
	// around for inspection. Defaults to 86400.
	// +kubebuilder:validation:Minimum=0
	// +optional
	TTLSecondsAfterFinished *int32 `json:"ttlSecondsAfterFinished,omitempty"`

	// resources are the migration container's resource requests and limits.
	// Defaults to the worker's resources.
	// +optional
	Resources *corev1.ResourceRequirements `json:"resources,omitempty"`

	// metadata is extra labels and annotations for the migration Job.
	// +optional
	Metadata *ObjectMeta `json:"metadata,omitempty"`
}

// TagStrategy selects how a branch is turned into a container image tag.
// +kubebuilder:validation:Enum=Immutable;Branch
type TagStrategy string

const (
	// TagStrategyImmutable picks the newest gh-<branch>-<timestamp>-<sha> tag.
	// Each build gets its own tag, so a new build is a real spec change that
	// triggers the migration gate and a rollout.
	TagStrategyImmutable TagStrategy = "Immutable"

	// TagStrategyBranch uses the moving gh-<branch> tag. The tag never
	// changes, so Kubernetes has no reason to restart pods and updates only
	// land when a pod is replaced for some other reason. Only useful with an
	// Always pull policy.
	TagStrategyBranch TagStrategy = "Branch"
)

// AutoUpdateSpec keeps authentik tracking a git branch by resolving that
// branch's newest published container image and rolling it out.
type AutoUpdateSpec struct {
	// enabled turns on branch tracking. While enabled, global.image.tag is
	// managed by the operator and any value set there is ignored.
	// +optional
	Enabled bool `json:"enabled,omitempty"`

	// branch is the git branch to track, e.g. main or version-2026.8.
	// +optional
	Branch string `json:"branch,omitempty"`

	// repository is the image repository to look for tags in. Defaults to
	// global.image.repository.
	// +optional
	Repository string `json:"repository,omitempty"`

	// tagStrategy selects how the branch is turned into a tag. Defaults to
	// Immutable.
	// +optional
	TagStrategy TagStrategy `json:"tagStrategy,omitempty"`

	// interval is how often the registry is polled for new builds. Defaults
	// to 5m.
	// +optional
	Interval *metav1.Duration `json:"interval,omitempty"`

	// pullSecret holds registry credentials for listing tags in a private
	// repository. Must be a dockerconfigjson Secret in the same namespace.
	// +optional
	PullSecret *corev1.LocalObjectReference `json:"pullSecret,omitempty"`
}

// AuthentikSpec defines the desired state of Authentik.
//
// Everything except releaseName, migrations, autoUpdate, reconcileInterval and
// prune uses the authentik Helm chart's values.yaml key names, so a values file
// can be moved into this spec as-is.
type AuthentikSpec struct {
	// releaseName prefixes every object the operator creates. It matches the
	// Helm release name, so an existing chart install is adopted rather than
	// duplicated. Immutable; defaults to the Authentik object's own name.
	// +kubebuilder:validation:MaxLength=53
	// +kubebuilder:validation:Pattern=`^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`
	// +kubebuilder:validation:XValidation:rule="self == oldSelf",message="releaseName is immutable"
	// +optional
	ReleaseName string `json:"releaseName,omitempty"`

	// migrations controls the database migration Job that gates upgrades.
	// +optional
	Migrations *MigrationsSpec `json:"migrations,omitempty"`

	// autoUpdate keeps authentik tracking a git branch.
	// +optional
	AutoUpdate *AutoUpdateSpec `json:"autoUpdate,omitempty"`

	// reconcileInterval is how often the desired state is re-applied to
	// correct drift. Defaults to 5m.
	// +optional
	ReconcileInterval *metav1.Duration `json:"reconcileInterval,omitempty"`

	// prune deletes objects the operator previously created that are no longer
	// part of the desired state, for instance after disabling the Ingress.
	// Defaults to true. Turning it off leaves such objects behind.
	// +optional
	Prune *bool `json:"prune,omitempty"`

	// nameOverride replaces the "authentik" name used to build object names.
	// Prefer global.nameOverride.
	// +optional
	NameOverride string `json:"nameOverride,omitempty"`

	// fullnameOverride fully replaces the generated object name prefix. Prefer
	// global.fullnameOverride.
	// +optional
	FullnameOverride string `json:"fullnameOverride,omitempty"`

	// global holds configuration shared by every authentik component.
	// +optional
	Global *GlobalSpec `json:"global,omitempty"`

	// authentik is the authentik application configuration.
	// +optional
	Authentik *AuthentikConfigSpec `json:"authentik,omitempty"`

	// blueprints mounts extra blueprints into the worker.
	// +optional
	Blueprints *BlueprintsSpec `json:"blueprints,omitempty"`

	// server configures the authentik server and how traffic reaches it.
	// +optional
	Server *ServerSpec `json:"server,omitempty"`

	// worker configures the authentik worker.
	// +optional
	Worker *WorkerSpec `json:"worker,omitempty"`

	// serviceAccount configures the ServiceAccount and RBAC the worker uses
	// to manage outposts in this cluster.
	// +optional
	ServiceAccount *ServiceAccountSpec `json:"serviceAccount,omitempty"`

	// geoip configures the geoipupdate sidecar.
	// +optional
	GeoIP *GeoIPSpec `json:"geoip,omitempty"`

	// prometheus configures the shipped alerting rules.
	// +optional
	Prometheus *PrometheusSpec `json:"prometheus,omitempty"`

	// postgresql configures the optional bundled PostgreSQL database.
	// +optional
	PostgreSQL *PostgreSQLSpec `json:"postgresql,omitempty"`
}

// Condition types set on an Authentik resource.
const (
	// ConditionReady is true once the desired version is deployed.
	ConditionReady = "Ready"

	// ConditionProgressing is true while the operator is working towards the
	// desired state.
	ConditionProgressing = "Progressing"

	// ConditionDegraded is true when the operator could not reach the desired
	// state.
	ConditionDegraded = "Degraded"

	// ConditionMigrated reports the state of the database migration Job that
	// gates upgrades.
	ConditionMigrated = "Migrated"

	// ConditionDeployed reports whether the desired objects are applied.
	ConditionDeployed = "Deployed"
)

// Phase is a coarse, human-facing summary of what the operator is doing.
// +kubebuilder:validation:Enum=Migrating;Deploying;Ready;Failed
type Phase string

const (
	// PhaseMigrating means the migration Job is running and the rollout is
	// held back until it finishes.
	PhaseMigrating Phase = "Migrating"

	// PhaseDeploying means the desired objects are being applied.
	PhaseDeploying Phase = "Deploying"

	// PhaseReady means the desired version is deployed.
	PhaseReady Phase = "Ready"

	// PhaseFailed means the operator could not reach the desired state.
	PhaseFailed Phase = "Failed"
)

// AppliedStatus records what the last successful reconcile put in the cluster.
type AppliedStatus struct {
	// objects counts the objects the operator applied.
	// +optional
	Objects int32 `json:"objects,omitempty"`

	// pruned counts the objects the last reconcile deleted because they are no
	// longer part of the desired state.
	// +optional
	Pruned int32 `json:"pruned,omitempty"`

	// skipped names the objects whose kind is not installed in this cluster,
	// which is how an optional ServiceMonitor or HTTPRoute reports itself.
	// +optional
	Skipped []string `json:"skipped,omitempty"`

	// lastAppliedAt is when the desired state was last applied.
	// +optional
	LastAppliedAt *metav1.Time `json:"lastAppliedAt,omitempty"`
}

// AuthentikStatus defines the observed state of Authentik.
type AuthentikStatus struct {
	// conditions represent the current state of the Authentik resource.
	//
	// Condition types:
	// - "Ready": the desired version is deployed
	// - "Progressing": the operator is working towards the desired state
	// - "Degraded": the operator could not reach the desired state
	// - "Migrated": state of the migration Job that gates upgrades
	// - "Deployed": state of the applied objects
	// +listType=map
	// +listMapKey=type
	// +optional
	Conditions []metav1.Condition `json:"conditions,omitempty"`

	// observedGeneration is the spec generation this status was computed from.
	// +optional
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`

	// phase is a coarse summary of what the operator is doing.
	// +optional
	Phase Phase `json:"phase,omitempty"`

	// applied records what the last successful reconcile put in the cluster.
	// +optional
	Applied *AppliedStatus `json:"applied,omitempty"`

	// resolvedImage is the full image reference the operator is deploying,
	// including the tag it resolved.
	// +optional
	ResolvedImage string `json:"resolvedImage,omitempty"`

	// deployedVersion is the image tag currently rolled out.
	// +optional
	DeployedVersion string `json:"deployedVersion,omitempty"`

	// migratedVersion is the image tag migrations last completed for. The
	// rollout is held back whenever this trails the resolved version.
	// +optional
	MigratedVersion string `json:"migratedVersion,omitempty"`

	// migrationJob is the name of the migration Job for the version currently
	// being rolled out.
	// +optional
	MigrationJob string `json:"migrationJob,omitempty"`

	// appliedHash fingerprints the desired state that was last applied. The
	// operator compares it against the current desired state to tell a real
	// change from a periodic re-reconcile, so that re-reading its own status
	// does not trigger another apply.
	// +optional
	AppliedHash string `json:"appliedHash,omitempty"`

	// lastResolvedAt is when the image tag was last resolved from the
	// registry. Only set while autoUpdate is enabled.
	// +optional
	LastResolvedAt *metav1.Time `json:"lastResolvedAt,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:resource:scope=Namespaced,shortName=ak
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=".status.phase"
// +kubebuilder:printcolumn:name="Version",type=string,JSONPath=".status.deployedVersion"
// +kubebuilder:printcolumn:name="Objects",type=integer,JSONPath=".status.applied.objects"
// +kubebuilder:printcolumn:name="Ready",type=string,JSONPath=".status.conditions[?(@.type=='Ready')].status"
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=".metadata.creationTimestamp"

// Authentik is the Schema for the authentiks API
type Authentik struct {
	metav1.TypeMeta `json:",inline"`

	// metadata is a standard object metadata
	// +optional
	metav1.ObjectMeta `json:"metadata,omitzero"`

	// spec defines the desired state of Authentik
	// +required
	Spec AuthentikSpec `json:"spec"`

	// status defines the observed state of Authentik
	// +optional
	Status AuthentikStatus `json:"status,omitzero"`
}

// +kubebuilder:object:root=true

// AuthentikList contains a list of Authentik
type AuthentikList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitzero"`
	Items           []Authentik `json:"items"`
}

func init() {
	SchemeBuilder.Register(func(s *runtime.Scheme) error {
		s.AddKnownTypes(SchemeGroupVersion, &Authentik{}, &AuthentikList{})
		return nil
	})
}
