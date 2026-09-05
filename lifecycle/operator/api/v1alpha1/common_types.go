package v1alpha1

import (
	autoscalingv2 "k8s.io/api/autoscaling/v2"
	corev1 "k8s.io/api/core/v1"
	networkingv1 "k8s.io/api/networking/v1"
	apiextensionsv1 "k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
)

// The JSON tags in this file deliberately match the keys of the authentik Helm
// chart's values.yaml rather than Kubernetes' usual camelCase, so that a chart
// values file can be moved into an Authentik spec unchanged. The operator no
// longer renders the chart, but staying key-compatible keeps that migration
// path open.
//
// Fields typed as apiextensionsv1.JSON belong to APIs this operator does not
// depend on -- the Prometheus Operator and the Gateway API -- and are copied
// verbatim into an unstructured object.

// ImageSpec selects a container image.
type ImageSpec struct {
	// repository is the image repository, without a tag.
	// +optional
	Repository string `json:"repository,omitempty"`

	// tag is the image tag. Defaults to the chart's appVersion.
	// +optional
	Tag string `json:"tag,omitempty"`

	// digest pins the image by digest. Takes precedence over tag.
	// +optional
	Digest string `json:"digest,omitempty"`

	// pullPolicy is the image pull policy.
	// +kubebuilder:validation:Enum=Always;Never;IfNotPresent
	// +optional
	PullPolicy corev1.PullPolicy `json:"pullPolicy,omitempty"`
}

// NodeAffinityPreset configures the generated node affinity rules.
type NodeAffinityPreset struct {
	// type selects how strictly matchExpressions are applied.
	// +kubebuilder:validation:Enum=none;soft;hard
	// +optional
	Type string `json:"type,omitempty"`

	// matchExpressions are the node selector requirements to match.
	// +optional
	MatchExpressions []corev1.NodeSelectorRequirement `json:"matchExpressions,omitempty"`
}

// AffinityPreset configures the affinity rules the chart generates for
// components that do not set an explicit affinity of their own.
type AffinityPreset struct {
	// podAntiAffinity spreads replicas across nodes (soft) or across nodes and
	// availability zones (hard).
	// +kubebuilder:validation:Enum=none;soft;hard
	// +optional
	PodAntiAffinity string `json:"podAntiAffinity,omitempty"`

	// nodeAffinity restricts which nodes components may be scheduled on.
	// +optional
	NodeAffinity *NodeAffinityPreset `json:"nodeAffinity,omitempty"`
}

// DeploymentStrategy is the rollout strategy applied to the generated
// Deployments. rollingUpdate is ignored when type is Recreate.
type DeploymentStrategy struct {
	// type is the rollout strategy type.
	// +kubebuilder:validation:Enum=Recreate;RollingUpdate
	// +optional
	Type string `json:"type,omitempty"`

	// rollingUpdate tunes the RollingUpdate strategy.
	// +optional
	RollingUpdate *RollingUpdate `json:"rollingUpdate,omitempty"`
}

// RollingUpdate tunes a RollingUpdate deployment strategy.
type RollingUpdate struct {
	// maxSurge is the number or percentage of pods that may be created above
	// the desired replica count.
	// +optional
	MaxSurge *intstr.IntOrString `json:"maxSurge,omitempty"`

	// maxUnavailable is the number or percentage of pods that may be
	// unavailable during the update.
	// +optional
	MaxUnavailable *intstr.IntOrString `json:"maxUnavailable,omitempty"`
}

// GlobalSpec holds configuration shared by every authentik component. Each
// component may override most of these individually.
type GlobalSpec struct {
	// nameOverride replaces the "authentik" name used to build object names.
	// +optional
	NameOverride string `json:"nameOverride,omitempty"`

	// fullnameOverride fully replaces the generated object name prefix.
	// +optional
	FullnameOverride string `json:"fullnameOverride,omitempty"`

	// namespaceOverride deploys the chart's objects into a different namespace
	// than the Authentik resource lives in.
	// +optional
	NamespaceOverride string `json:"namespaceOverride,omitempty"`

	// additionalLabels are applied to every object the operator creates.
	// +optional
	AdditionalLabels map[string]string `json:"additionalLabels,omitempty"`

	// revisionHistoryLimit is the number of old ReplicaSets to retain per
	// Deployment.
	// +optional
	RevisionHistoryLimit *int32 `json:"revisionHistoryLimit,omitempty"`

	// image is the default image for all authentik components. The tag is
	// managed by the operator when autoUpdate is enabled.
	// +optional
	Image *ImageSpec `json:"image,omitempty"`

	// imagePullSecrets holds credentials for pulling from a private registry.
	// +optional
	ImagePullSecrets []corev1.LocalObjectReference `json:"imagePullSecrets,omitempty"`

	// deploymentAnnotations are added to every Deployment.
	// +optional
	DeploymentAnnotations map[string]string `json:"deploymentAnnotations,omitempty"`

	// podAnnotations are added to every pod.
	// +optional
	PodAnnotations map[string]string `json:"podAnnotations,omitempty"`

	// secretAnnotations are added to every Secret.
	// +optional
	SecretAnnotations map[string]string `json:"secretAnnotations,omitempty"`

	// podLabels are added to every pod.
	// +optional
	PodLabels map[string]string `json:"podLabels,omitempty"`

	// addPrometheusAnnotations adds scrape annotations to the metrics Services,
	// as an alternative to ServiceMonitors.
	// +optional
	AddPrometheusAnnotations *bool `json:"addPrometheusAnnotations,omitempty"`

	// securityContext is the default pod-level security context.
	// +optional
	SecurityContext *corev1.PodSecurityContext `json:"securityContext,omitempty"`

	// hostAliases are injected into every pod's hosts file.
	// +optional
	HostAliases []corev1.HostAlias `json:"hostAliases,omitempty"`

	// priorityClassName is the default priority class for all components.
	// +optional
	PriorityClassName string `json:"priorityClassName,omitempty"`

	// nodeSelector is the default node selector for all components.
	// +optional
	NodeSelector map[string]string `json:"nodeSelector,omitempty"`

	// tolerations are the default tolerations for all components.
	// +optional
	Tolerations []corev1.Toleration `json:"tolerations,omitempty"`

	// affinity is the default affinity preset for components that do not set
	// their own affinity.
	// +optional
	Affinity *AffinityPreset `json:"affinity,omitempty"`

	// topologySpreadConstraints are the default spread constraints for all
	// components.
	// +optional
	TopologySpreadConstraints []corev1.TopologySpreadConstraint `json:"topologySpreadConstraints,omitempty"`

	// deploymentStrategy is the default rollout strategy for all Deployments.
	// +optional
	DeploymentStrategy *DeploymentStrategy `json:"deploymentStrategy,omitempty"`

	// env are extra environment variables for all authentik components. Does
	// not apply to the GeoIP sidecar.
	// +optional
	Env []corev1.EnvVar `json:"env,omitempty"`

	// envFrom are extra environment sources for all authentik components. Does
	// not apply to the GeoIP sidecar.
	// +optional
	EnvFrom []corev1.EnvFromSource `json:"envFrom,omitempty"`

	// volumeMounts are extra mounts for all authentik containers. Does not
	// apply to the GeoIP sidecar.
	// +optional
	VolumeMounts []corev1.VolumeMount `json:"volumeMounts,omitempty"`

	// volumes are extra volumes for all authentik pods.
	// +optional
	Volumes []corev1.Volume `json:"volumes,omitempty"`
}

// AutoscalingSpec configures a HorizontalPodAutoscaler for a component.
type AutoscalingSpec struct {
	// enabled deploys a HorizontalPodAutoscaler. When set, the component's
	// replicas field is ignored.
	// +optional
	Enabled bool `json:"enabled,omitempty"`

	// annotations are added to the HorizontalPodAutoscaler.
	// +optional
	Annotations map[string]string `json:"annotations,omitempty"`

	// minReplicas is the lower bound on replicas.
	// +kubebuilder:validation:Minimum=1
	// +optional
	MinReplicas *int32 `json:"minReplicas,omitempty"`

	// maxReplicas is the upper bound on replicas.
	// +kubebuilder:validation:Minimum=1
	// +optional
	MaxReplicas *int32 `json:"maxReplicas,omitempty"`

	// targetCPUUtilizationPercentage is the average CPU utilization to target.
	// Ignored when metrics is set.
	// +optional
	TargetCPUUtilizationPercentage *int32 `json:"targetCPUUtilizationPercentage,omitempty"`

	// targetMemoryUtilizationPercentage is the average memory utilization to
	// target. Ignored when metrics is set.
	// +optional
	TargetMemoryUtilizationPercentage *int32 `json:"targetMemoryUtilizationPercentage,omitempty"`

	// behavior configures scale-up and scale-down behavior.
	// +optional
	Behavior *autoscalingv2.HorizontalPodAutoscalerBehavior `json:"behavior,omitempty"`

	// metrics replaces the target utilization fields with custom HPA metrics.
	// +optional
	Metrics []autoscalingv2.MetricSpec `json:"metrics,omitempty"`
}

// PDBSpec configures a PodDisruptionBudget for a component.
type PDBSpec struct {
	// enabled deploys a PodDisruptionBudget.
	// +optional
	Enabled bool `json:"enabled,omitempty"`

	// labels are added to the PodDisruptionBudget.
	// +optional
	Labels map[string]string `json:"labels,omitempty"`

	// annotations are added to the PodDisruptionBudget.
	// +optional
	Annotations map[string]string `json:"annotations,omitempty"`

	// minAvailable is the number or percentage of pods that must remain
	// available. Defaults to 0 when neither bound is set.
	// +optional
	MinAvailable *intstr.IntOrString `json:"minAvailable,omitempty"`

	// maxUnavailable is the number or percentage of pods that may be
	// unavailable. Takes precedence over minAvailable.
	// +optional
	MaxUnavailable *intstr.IntOrString `json:"maxUnavailable,omitempty"`
}

// ServiceMonitorSpec configures a Prometheus Operator ServiceMonitor.
type ServiceMonitorSpec struct {
	// enabled deploys a ServiceMonitor. Requires the Prometheus Operator CRDs.
	// +optional
	Enabled bool `json:"enabled,omitempty"`

	// interval is how often Prometheus scrapes the target.
	// +optional
	Interval string `json:"interval,omitempty"`

	// scrapeTimeout is the per-scrape timeout.
	// +optional
	ScrapeTimeout string `json:"scrapeTimeout,omitempty"`

	// relabelings are applied to the discovered targets.
	// +optional
	Relabelings []apiextensionsv1.JSON `json:"relabelings,omitempty"`

	// metricRelabelings are applied to the scraped samples.
	// +optional
	MetricRelabelings []apiextensionsv1.JSON `json:"metricRelabelings,omitempty"`

	// selector overrides the Service selector of the ServiceMonitor.
	// +optional
	Selector map[string]string `json:"selector,omitempty"`

	// scheme is the scheme Prometheus uses to scrape, e.g. http or https.
	// +optional
	Scheme string `json:"scheme,omitempty"`

	// tlsConfig is the TLS configuration Prometheus uses to scrape.
	// +optional
	TLSConfig *apiextensionsv1.JSON `json:"tlsConfig,omitempty"`

	// namespace deploys the ServiceMonitor into a different namespace.
	// +optional
	Namespace string `json:"namespace,omitempty"`

	// labels are added to the ServiceMonitor.
	// +optional
	Labels map[string]string `json:"labels,omitempty"`

	// annotations are added to the ServiceMonitor.
	// +optional
	Annotations map[string]string `json:"annotations,omitempty"`
}

// MetricsServiceSpec configures the Service placed in front of a component's
// metrics port.
type MetricsServiceSpec struct {
	// type is the Service type.
	// +optional
	Type corev1.ServiceType `json:"type,omitempty"`

	// clusterIP is the Service cluster IP. "None" makes it headless.
	// +optional
	ClusterIP string `json:"clusterIP,omitempty"`

	// annotations are added to the metrics Service.
	// +optional
	Annotations map[string]string `json:"annotations,omitempty"`

	// labels are added to the metrics Service.
	// +optional
	Labels map[string]string `json:"labels,omitempty"`

	// servicePort is the port the metrics Service listens on.
	// +optional
	ServicePort *int32 `json:"servicePort,omitempty"`

	// portName is the name of the metrics Service port.
	// +optional
	PortName string `json:"portName,omitempty"`
}

// MetricsSpec configures metrics exposure for a component.
type MetricsSpec struct {
	// enabled deploys a Service in front of the component's metrics port.
	// +optional
	Enabled bool `json:"enabled,omitempty"`

	// service configures the metrics Service.
	// +optional
	Service *MetricsServiceSpec `json:"service,omitempty"`

	// serviceMonitor configures a Prometheus Operator ServiceMonitor.
	// +optional
	ServiceMonitor *ServiceMonitorSpec `json:"serviceMonitor,omitempty"`
}

// ComponentSpec holds the settings shared by the server and worker
// Deployments. Fields left empty fall back to the matching global value.
type ComponentSpec struct {
	// enabled deploys this component.
	// +optional
	Enabled *bool `json:"enabled,omitempty"`

	// name is the component name, used as the object name suffix, the
	// app.kubernetes.io/component label and the container name.
	// +optional
	Name string `json:"name,omitempty"`

	// replicas is the number of pods to run. Ignored when autoscaling is
	// enabled.
	// +kubebuilder:validation:Minimum=0
	// +optional
	Replicas *int32 `json:"replicas,omitempty"`

	// autoscaling configures a HorizontalPodAutoscaler for this component.
	// +optional
	Autoscaling *AutoscalingSpec `json:"autoscaling,omitempty"`

	// pdb configures a PodDisruptionBudget for this component.
	// +optional
	PDB *PDBSpec `json:"pdb,omitempty"`

	// image overrides the global image for this component. Server and worker
	// should always run the same image.
	// +optional
	Image *ImageSpec `json:"image,omitempty"`

	// imagePullSecrets overrides global.imagePullSecrets for this component.
	// +optional
	ImagePullSecrets []corev1.LocalObjectReference `json:"imagePullSecrets,omitempty"`

	// env are extra environment variables for this component, appended after
	// global.env.
	// +optional
	Env []corev1.EnvVar `json:"env,omitempty"`

	// envFrom are extra environment sources for this component, appended after
	// global.envFrom.
	// +optional
	EnvFrom []corev1.EnvFromSource `json:"envFrom,omitempty"`

	// lifecycle sets postStart and preStop hooks on the main container.
	// +optional
	Lifecycle *corev1.Lifecycle `json:"lifecycle,omitempty"`

	// extraContainers are sidecars added to this component's pod.
	// +optional
	ExtraContainers []corev1.Container `json:"extraContainers,omitempty"`

	// initContainers are init containers added to this component's pod.
	// +optional
	InitContainers []corev1.Container `json:"initContainers,omitempty"`

	// volumeMounts are extra mounts for this component's main container.
	// +optional
	VolumeMounts []corev1.VolumeMount `json:"volumeMounts,omitempty"`

	// volumes are extra volumes for this component's pod.
	// +optional
	Volumes []corev1.Volume `json:"volumes,omitempty"`

	// deploymentAnnotations are added to this component's Deployment.
	// +optional
	DeploymentAnnotations map[string]string `json:"deploymentAnnotations,omitempty"`

	// podAnnotations are added to this component's pods.
	// +optional
	PodAnnotations map[string]string `json:"podAnnotations,omitempty"`

	// podLabels are added to this component's pods.
	// +optional
	PodLabels map[string]string `json:"podLabels,omitempty"`

	// resources are the resource requests and limits for the main container.
	// +optional
	Resources *corev1.ResourceRequirements `json:"resources,omitempty"`

	// hostNetwork runs this component's pods on the host network.
	// +optional
	HostNetwork *bool `json:"hostNetwork,omitempty"`

	// dnsConfig is the pod DNS configuration.
	// +optional
	DNSConfig *corev1.PodDNSConfig `json:"dnsConfig,omitempty"`

	// dnsPolicy overrides the pod DNS policy.
	// +optional
	DNSPolicy corev1.DNSPolicy `json:"dnsPolicy,omitempty"`

	// serviceAccountName is the ServiceAccount this component's pods run as.
	// +optional
	ServiceAccountName string `json:"serviceAccountName,omitempty"`

	// automountServiceAccountToken controls token automounting. Only applies
	// when serviceAccountName is set.
	// +optional
	AutomountServiceAccountToken *bool `json:"automountServiceAccountToken,omitempty"`

	// securityContext is this component's pod-level security context.
	// +optional
	SecurityContext *corev1.PodSecurityContext `json:"securityContext,omitempty"`

	// containerSecurityContext is the main container's security context.
	// +optional
	ContainerSecurityContext *corev1.SecurityContext `json:"containerSecurityContext,omitempty"`

	// livenessProbe overrides the main container's liveness probe.
	// +optional
	LivenessProbe *corev1.Probe `json:"livenessProbe,omitempty"`

	// readinessProbe overrides the main container's readiness probe.
	// +optional
	ReadinessProbe *corev1.Probe `json:"readinessProbe,omitempty"`

	// startupProbe overrides the main container's startup probe.
	// +optional
	StartupProbe *corev1.Probe `json:"startupProbe,omitempty"`

	// terminationGracePeriodSeconds is how long pods get to shut down.
	// +optional
	TerminationGracePeriodSeconds *int64 `json:"terminationGracePeriodSeconds,omitempty"`

	// priorityClassName overrides global.priorityClassName.
	// +optional
	PriorityClassName string `json:"priorityClassName,omitempty"`

	// nodeSelector overrides global.nodeSelector.
	// +optional
	NodeSelector map[string]string `json:"nodeSelector,omitempty"`

	// tolerations override global.tolerations.
	// +optional
	Tolerations []corev1.Toleration `json:"tolerations,omitempty"`

	// affinity replaces the generated affinity preset for this component.
	// +optional
	Affinity *corev1.Affinity `json:"affinity,omitempty"`

	// topologySpreadConstraints override global.topologySpreadConstraints.
	// +optional
	TopologySpreadConstraints []corev1.TopologySpreadConstraint `json:"topologySpreadConstraints,omitempty"`

	// deploymentStrategy overrides global.deploymentStrategy.
	// +optional
	DeploymentStrategy *DeploymentStrategy `json:"deploymentStrategy,omitempty"`

	// metrics configures metrics exposure for this component.
	// +optional
	Metrics *MetricsSpec `json:"metrics,omitempty"`
}

// ServerContainerPorts are the ports the server container listens on.
type ServerContainerPorts struct {
	// http is the plaintext HTTP port.
	// +optional
	HTTP *int32 `json:"http,omitempty"`

	// https is the TLS port.
	// +optional
	HTTPS *int32 `json:"https,omitempty"`

	// metrics is the Prometheus metrics port.
	// +optional
	Metrics *int32 `json:"metrics,omitempty"`
}

// WorkerContainerPorts are the ports the worker container listens on.
type WorkerContainerPorts struct {
	// http is the plaintext HTTP port.
	// +optional
	HTTP *int32 `json:"http,omitempty"`

	// metrics is the Prometheus metrics port.
	// +optional
	Metrics *int32 `json:"metrics,omitempty"`
}

// ServerServiceSpec configures the Service in front of the authentik server.
type ServerServiceSpec struct {
	// annotations are added to the Service.
	// +optional
	Annotations map[string]string `json:"annotations,omitempty"`

	// labels are added to the Service.
	// +optional
	Labels map[string]string `json:"labels,omitempty"`

	// type is the Service type.
	// +optional
	Type corev1.ServiceType `json:"type,omitempty"`

	// clusterIP is the Service cluster IP. Only used when type is ClusterIP.
	// +optional
	ClusterIP string `json:"clusterIP,omitempty"`

	// nodePortHttp is the HTTP node port. Only used when type is NodePort.
	// +optional
	NodePortHTTP *int32 `json:"nodePortHttp,omitempty"`

	// nodePortHttps is the HTTPS node port. Only used when type is NodePort.
	// +optional
	NodePortHTTPS *int32 `json:"nodePortHttps,omitempty"`

	// servicePortHttp is the HTTP Service port.
	// +optional
	ServicePortHTTP *int32 `json:"servicePortHttp,omitempty"`

	// servicePortHttps is the HTTPS Service port.
	// +optional
	ServicePortHTTPS *int32 `json:"servicePortHttps,omitempty"`

	// servicePortHttpName is the name of the HTTP Service port.
	// +optional
	ServicePortHTTPName string `json:"servicePortHttpName,omitempty"`

	// servicePortHttpsName is the name of the HTTPS Service port.
	// +optional
	ServicePortHTTPSName string `json:"servicePortHttpsName,omitempty"`

	// servicePortHttpAppProtocol sets appProtocol on the HTTP port.
	// +optional
	ServicePortHTTPAppProtocol string `json:"servicePortHttpAppProtocol,omitempty"`

	// servicePortHttpsAppProtocol sets appProtocol on the HTTPS port.
	// +optional
	ServicePortHTTPSAppProtocol string `json:"servicePortHttpsAppProtocol,omitempty"`

	// loadBalancerIP requests a specific IP. Only used when type is
	// LoadBalancer.
	// +optional
	LoadBalancerIP string `json:"loadBalancerIP,omitempty"`

	// loadBalancerSourceRanges restricts which sources may reach the
	// LoadBalancer.
	// +optional
	LoadBalancerSourceRanges []string `json:"loadBalancerSourceRanges,omitempty"`

	// externalIPs are additional IPs the Service accepts traffic on.
	// +optional
	ExternalIPs []string `json:"externalIPs,omitempty"`

	// externalTrafficPolicy routes external traffic to node-local or
	// cluster-wide endpoints.
	// +optional
	ExternalTrafficPolicy corev1.ServiceExternalTrafficPolicy `json:"externalTrafficPolicy,omitempty"`

	// sessionAffinity maintains session affinity. Supports ClientIP and None.
	// +optional
	SessionAffinity corev1.ServiceAffinity `json:"sessionAffinity,omitempty"`

	// sessionAffinityConfig tunes session affinity.
	// +optional
	SessionAffinityConfig *corev1.SessionAffinityConfig `json:"sessionAffinityConfig,omitempty"`

	// publishNotReadyAddresses routes traffic to pods that are not ready.
	// +optional
	PublishNotReadyAddresses *bool `json:"publishNotReadyAddresses,omitempty"`
}

// IngressSpec configures an Ingress in front of the authentik server.
type IngressSpec struct {
	// enabled deploys an Ingress.
	// +optional
	Enabled bool `json:"enabled,omitempty"`

	// annotations are added to the Ingress.
	// +optional
	Annotations map[string]string `json:"annotations,omitempty"`

	// labels are added to the Ingress.
	// +optional
	Labels map[string]string `json:"labels,omitempty"`

	// ingressClassName selects the ingress controller.
	// +optional
	IngressClassName string `json:"ingressClassName,omitempty"`

	// hosts are the hostnames to serve authentik on. When empty, a single
	// host-less rule is created.
	// +optional
	Hosts []string `json:"hosts,omitempty"`

	// paths are the paths to route to authentik. Defaults to
	// authentik.web.path.
	// +optional
	Paths []string `json:"paths,omitempty"`

	// pathType is the Ingress path type.
	// +kubebuilder:validation:Enum=Exact;Prefix;ImplementationSpecific
	// +optional
	PathType string `json:"pathType,omitempty"`

	// extraPaths are extra Ingress paths prepended to paths, for things like
	// cloud provider redirect rules.
	// +optional
	ExtraPaths []networkingv1.HTTPIngressPath `json:"extraPaths,omitempty"`

	// tls is the Ingress TLS configuration.
	// +optional
	TLS []networkingv1.IngressTLS `json:"tls,omitempty"`

	// https routes to the server's HTTPS port instead of HTTP.
	// +optional
	HTTPS *bool `json:"https,omitempty"`
}

// RouteSpec configures a Gateway API route in front of the authentik server.
type RouteSpec struct {
	// main is the primary route.
	// +optional
	Main *RouteMainSpec `json:"main,omitempty"`
}

// RouteMainSpec configures a Gateway API HTTPRoute.
type RouteMainSpec struct {
	// enabled deploys the route. Requires the Gateway API CRDs.
	// +optional
	Enabled bool `json:"enabled,omitempty"`

	// apiVersion is the Gateway API version to use.
	// +optional
	APIVersion string `json:"apiVersion,omitempty"`

	// kind is the route kind, e.g. HTTPRoute.
	// +optional
	Kind string `json:"kind,omitempty"`

	// annotations are added to the route.
	// +optional
	Annotations map[string]string `json:"annotations,omitempty"`

	// labels are added to the route.
	// +optional
	Labels map[string]string `json:"labels,omitempty"`

	// hostnames are the hostnames the route matches.
	// +optional
	Hostnames []string `json:"hostnames,omitempty"`

	// parentRefs are the Gateways this route attaches to.
	// +optional
	ParentRefs []apiextensionsv1.JSON `json:"parentRefs,omitempty"`

	// httpsRedirect adds a rule redirecting HTTP to HTTPS.
	// +optional
	HTTPSRedirect *bool `json:"httpsRedirect,omitempty"`

	// https routes to the server's HTTPS port instead of HTTP.
	// +optional
	HTTPS *bool `json:"https,omitempty"`

	// matches are the route match rules.
	// +optional
	Matches []apiextensionsv1.JSON `json:"matches,omitempty"`

	// filters are the route filters.
	// +optional
	Filters []apiextensionsv1.JSON `json:"filters,omitempty"`

	// additionalRules are extra rules appended to the route.
	// +optional
	AdditionalRules []apiextensionsv1.JSON `json:"additionalRules,omitempty"`
}

// ServerSpec configures the authentik server Deployment and everything routing
// traffic to it.
type ServerSpec struct {
	ComponentSpec `json:",inline"`

	// containerPorts are the ports the server container listens on.
	// +optional
	ContainerPorts *ServerContainerPorts `json:"containerPorts,omitempty"`

	// service configures the Service in front of the server.
	// +optional
	Service *ServerServiceSpec `json:"service,omitempty"`

	// ingress configures an Ingress in front of the server.
	// +optional
	Ingress *IngressSpec `json:"ingress,omitempty"`

	// route configures a Gateway API route in front of the server.
	// +optional
	Route *RouteSpec `json:"route,omitempty"`
}

// WorkerSpec configures the authentik worker Deployment.
type WorkerSpec struct {
	ComponentSpec `json:",inline"`

	// containerPorts are the ports the worker container listens on.
	// +optional
	ContainerPorts *WorkerContainerPorts `json:"containerPorts,omitempty"`
}

// BlueprintsSpec mounts extra blueprints into the worker. Only keys ending in
// .yaml are discovered and applied.
type BlueprintsSpec struct {
	// configMaps are the names of ConfigMaps to mount blueprints from.
	// +optional
	ConfigMaps []string `json:"configMaps,omitempty"`

	// secrets are the names of Secrets to mount blueprints from.
	// +optional
	Secrets []string `json:"secrets,omitempty"`
}

// GeoIPExistingSecret points at a Secret holding MaxMind credentials.
type GeoIPExistingSecret struct {
	// secretName is the name of the Secret holding the credentials.
	// +optional
	SecretName string `json:"secretName,omitempty"`

	// accountId is the Secret key holding the MaxMind account ID.
	// +optional
	AccountID string `json:"accountId,omitempty"`

	// licenseKey is the Secret key holding the MaxMind license key.
	// +optional
	LicenseKey string `json:"licenseKey,omitempty"`
}

// GeoIPSpec configures the geoipupdate sidecar that keeps the MaxMind
// databases current.
type GeoIPSpec struct {
	// enabled adds a geoipupdate sidecar to the server and worker pods.
	// +optional
	Enabled bool `json:"enabled,omitempty"`

	// editionIds is the space-separated list of MaxMind editions to download.
	// +optional
	EditionIDs string `json:"editionIds,omitempty"`

	// updateInterval is how often, in hours, the databases are refreshed.
	// +optional
	UpdateInterval *int32 `json:"updateInterval,omitempty"`

	// accountId is the MaxMind account ID. Ignored when existingSecret is set.
	// +optional
	AccountID string `json:"accountId,omitempty"`

	// licenseKey is the MaxMind license key. Ignored when existingSecret is
	// set.
	// +optional
	LicenseKey string `json:"licenseKey,omitempty"`

	// existingSecret reads the MaxMind credentials from an existing Secret
	// instead of the accountId and licenseKey fields.
	// +optional
	ExistingSecret *GeoIPExistingSecret `json:"existingSecret,omitempty"`

	// image is the geoipupdate image.
	// +optional
	Image *ImageSpec `json:"image,omitempty"`

	// env are extra environment variables for the sidecar.
	// +optional
	Env []corev1.EnvVar `json:"env,omitempty"`

	// envFrom are extra environment sources for the sidecar.
	// +optional
	EnvFrom []corev1.EnvFromSource `json:"envFrom,omitempty"`

	// volumeMounts are extra mounts for the sidecar.
	// +optional
	VolumeMounts []corev1.VolumeMount `json:"volumeMounts,omitempty"`

	// resources are the sidecar's resource requests and limits.
	// +optional
	Resources *corev1.ResourceRequirements `json:"resources,omitempty"`

	// containerSecurityContext is the sidecar's security context.
	// +optional
	ContainerSecurityContext *corev1.SecurityContext `json:"containerSecurityContext,omitempty"`
}

// PrometheusSpec configures the shipped Prometheus alerting rules.
type PrometheusSpec struct {
	// rules configures the PrometheusRule object.
	// +optional
	Rules *PrometheusRulesSpec `json:"rules,omitempty"`
}

// PrometheusRulesSpec configures the shipped PrometheusRule.
type PrometheusRulesSpec struct {
	// enabled deploys a PrometheusRule. Requires the Prometheus Operator CRDs.
	// +optional
	Enabled bool `json:"enabled,omitempty"`

	// namespace deploys the PrometheusRule into a different namespace.
	// +optional
	Namespace string `json:"namespace,omitempty"`

	// selector overrides the rule selector labels.
	// +optional
	Selector map[string]string `json:"selector,omitempty"`

	// labels are added to the PrometheusRule.
	// +optional
	Labels map[string]string `json:"labels,omitempty"`

	// annotations are added to the PrometheusRule.
	// +optional
	Annotations map[string]string `json:"annotations,omitempty"`

	// additionalRuleGroupAnnotations are added to every generated rule group.
	// +optional
	AdditionalRuleGroupAnnotations map[string]string `json:"additionalRuleGroupAnnotations,omitempty"`
}

// ServiceAccountSpec configures the ServiceAccount and RBAC the worker uses to
// manage outposts in this cluster.
type ServiceAccountSpec struct {
	// create deploys a ServiceAccount plus the Role and RoleBinding the worker
	// needs to manage Kubernetes outposts.
	// +optional
	Create *bool `json:"create,omitempty"`

	// annotations are added to the ServiceAccount.
	// +optional
	Annotations map[string]string `json:"annotations,omitempty"`

	// fullnameOverride overrides the generated ServiceAccount name.
	// +optional
	FullnameOverride string `json:"fullnameOverride,omitempty"`

	// serviceAccountSecret configures a long-lived token Secret for the
	// ServiceAccount.
	// +optional
	ServiceAccountSecret *ServiceAccountSecretSpec `json:"serviceAccountSecret,omitempty"`
}

// ServiceAccountSecretSpec configures a long-lived ServiceAccount token.
type ServiceAccountSecretSpec struct {
	// enabled creates a Secret holding a long-lived ServiceAccount token.
	// +optional
	Enabled bool `json:"enabled,omitempty"`
}

// ObjectMeta is the subset of metadata the operator sets on objects it builds
// itself, such as the migration Job.
type ObjectMeta struct {
	// labels are added to the object.
	// +optional
	Labels map[string]string `json:"labels,omitempty"`

	// annotations are added to the object.
	// +optional
	Annotations map[string]string `json:"annotations,omitempty"`
}
