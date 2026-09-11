package resources

import (
	"cmp"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"maps"
	"slices"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/utils/ptr"

	akv1alpha1 "goauthentik.io/lifecycle/operator/api/v1alpha1"
)

// component gathers everything that differs between the server and the worker,
// so the pod template itself is built once.
type component struct {
	spec akv1alpha1.ComponentSpec
	// name is the object name suffix and the app.kubernetes.io/component label.
	name string
	// objectName is the full name of this component's objects.
	objectName string
	// arg is the authentik subcommand the container runs.
	arg   string
	ports []corev1.ContainerPort
	// probes are the defaults for this component, before any spec override.
	liveness  *corev1.Probe
	readiness *corev1.Probe
	startup   *corev1.Probe
	// managesOutposts is true for the worker, which talks to the Kubernetes API
	// and so defaults to the outpost ServiceAccount.
	managesOutposts bool
	// mountsBlueprints is true for the worker, which is what applies them.
	mountsBlueprints bool
}

// ServerComponent describes the server, or nil when it is disabled.
func (b *Builder) ServerComponent() *component {
	spec := akv1alpha1.ComponentSpec{}
	var ports *akv1alpha1.ServerContainerPorts
	if s := b.Authentik.Spec.Server; s != nil {
		spec = s.ComponentSpec
		ports = s.ContainerPorts
	}
	if spec.Enabled != nil && !*spec.Enabled {
		return nil
	}

	http, https, metrics := defaultHTTPPort, defaultHTTPSPort, defaultMetricsPort
	if ports != nil {
		http = ptr.Deref(ports.HTTP, http)
		https = ptr.Deref(ports.HTTPS, https)
		metrics = ptr.Deref(ports.Metrics, metrics)
	}

	path := b.webPath()
	return &component{
		spec:       spec,
		name:       b.Authentik.ServerComponentName(),
		objectName: b.ServerName(),
		arg:        serverComponent,
		ports: []corev1.ContainerPort{
			{Name: "http", ContainerPort: http, Protocol: corev1.ProtocolTCP},
			{Name: "https", ContainerPort: https, Protocol: corev1.ProtocolTCP},
			{Name: defaultMetricsPortName, ContainerPort: metrics, Protocol: corev1.ProtocolTCP},
		},
		liveness:  httpProbe(path+"-/health/live/", defaultProbeFailureThreshold, defaultProbeInitialDelay),
		readiness: httpProbe(path+"-/health/ready/", defaultProbeFailureThreshold, defaultProbeInitialDelay),
		startup:   httpProbe(path+"-/health/live/", defaultStartupFailureThreshold, defaultProbeInitialDelay),
	}
}

// WorkerComponent describes the worker, or nil when it is disabled.
func (b *Builder) WorkerComponent() *component {
	spec := akv1alpha1.ComponentSpec{}
	var ports *akv1alpha1.WorkerContainerPorts
	if w := b.Authentik.Spec.Worker; w != nil {
		spec = w.ComponentSpec
		ports = w.ContainerPorts
	}
	if spec.Enabled != nil && !*spec.Enabled {
		return nil
	}

	http, metrics := defaultHTTPPort, defaultMetricsPort
	if ports != nil {
		http = ptr.Deref(ports.HTTP, http)
		metrics = ptr.Deref(ports.Metrics, metrics)
	}

	return &component{
		spec:       spec,
		name:       b.Authentik.WorkerComponentName(),
		objectName: b.WorkerName(),
		arg:        workerComponent,
		ports: []corev1.ContainerPort{
			{Name: "http", ContainerPort: http, Protocol: corev1.ProtocolTCP},
			{Name: defaultMetricsPortName, ContainerPort: metrics, Protocol: corev1.ProtocolTCP},
		},
		liveness:         execProbe(defaultProbeFailureThreshold, defaultProbeInitialDelay),
		readiness:        execProbe(defaultProbeFailureThreshold, defaultProbeInitialDelay),
		startup:          execProbe(defaultStartupFailureThreshold, defaultWorkerStartupInitialDelay),
		managesOutposts:  true,
		mountsBlueprints: true,
	}
}

func (b *Builder) Deployment(c *component) (*appsv1.Deployment, error) {
	global := b.global()

	template, err := b.podTemplate(c)
	if err != nil {
		return nil, err
	}

	strategy, err := b.strategy(c)
	if err != nil {
		return nil, err
	}

	deployment := &appsv1.Deployment{
		ObjectMeta: b.objectMeta(c.objectName, c.name, nil,
			mergedMap(global.DeploymentAnnotations, c.spec.DeploymentAnnotations)),
		Spec: appsv1.DeploymentSpec{
			RevisionHistoryLimit: ptr.To(ptr.Deref(global.RevisionHistoryLimit, defaultRevisionHistoryLimit)),
			Selector:             &metav1.LabelSelector{MatchLabels: b.SelectorLabels(c.name)},
			Template:             *template,
			Strategy:             strategy,
		},
	}

	// Leaving replicas unset hands the count to the HorizontalPodAutoscaler;
	// setting both would have the two fight over it.
	if c.spec.Autoscaling == nil || !c.spec.Autoscaling.Enabled {
		deployment.Spec.Replicas = ptr.To(ptr.Deref(c.spec.Replicas, defaultReplicas))
	}

	return deployment, nil
}

func (b *Builder) podTemplate(c *component) (*corev1.PodTemplateSpec, error) {
	global := b.global()

	podLabels := b.Labels(c.name)
	maps.Copy(podLabels, mergedMap(global.PodLabels, c.spec.PodLabels))

	podAnnotations := map[string]string{}
	maps.Copy(podAnnotations, mergedMap(global.PodAnnotations, c.spec.PodAnnotations))
	// Restart the pods when the configuration changes. Without this a Secret
	// edit would sit unread until something else replaced them.
	checksum, err := b.configChecksum()
	if err != nil {
		return nil, err
	}
	if checksum != "" {
		podAnnotations[configChecksumAnnotation] = checksum
	}

	containers := []corev1.Container{*b.mainContainer(c)}
	if sidecar := b.geoipSidecar(); sidecar != nil {
		containers = append(containers, *sidecar)
	}
	containers = append(containers, c.spec.ExtraContainers...)

	securityContext, err := mergeStructs(global.SecurityContext, c.spec.SecurityContext)
	if err != nil {
		return nil, err
	}

	nodeSelector := c.spec.NodeSelector
	if len(nodeSelector) == 0 {
		nodeSelector = global.NodeSelector
	}

	spec := corev1.PodSpec{
		Containers:                    containers,
		InitContainers:                c.spec.InitContainers,
		ImagePullSecrets:              firstNonEmpty(c.spec.ImagePullSecrets, global.ImagePullSecrets),
		HostAliases:                   global.HostAliases,
		SecurityContext:               securityContext,
		PriorityClassName:             cmp.Or(c.spec.PriorityClassName, global.PriorityClassName),
		Affinity:                      b.affinity(c),
		NodeSelector:                  nodeSelector,
		Tolerations:                   firstNonEmpty(c.spec.Tolerations, global.Tolerations),
		TopologySpreadConstraints:     b.topologySpreadConstraints(c),
		Volumes:                       b.volumes(c),
		DNSConfig:                     c.spec.DNSConfig,
		DNSPolicy:                     c.spec.DNSPolicy,
		TerminationGracePeriodSeconds: ptr.To(ptr.Deref(c.spec.TerminationGracePeriodSeconds, defaultTerminationGracePeriod)),
		EnableServiceLinks:            ptr.To(true),
	}

	if c.spec.HostNetwork != nil {
		spec.HostNetwork = *c.spec.HostNetwork
	}

	if name := b.serviceAccountFor(c); name != "" {
		spec.ServiceAccountName = name
		spec.AutomountServiceAccountToken = c.spec.AutomountServiceAccountToken
	}

	return &corev1.PodTemplateSpec{
		ObjectMeta: metav1.ObjectMeta{Labels: podLabels, Annotations: nilIfEmpty(podAnnotations)},
		Spec:       spec,
	}, nil
}

func (b *Builder) mainContainer(c *component) *corev1.Container {
	global := b.global()

	env := slices.Concat(global.Env, c.spec.Env)

	envFrom := []corev1.EnvFromSource{}
	// Injected whether the operator renders the Secret or the user supplies
	// it; only skipped when the configuration is disabled outright.
	if b.configSecretMounted() {
		envFrom = append(envFrom, corev1.EnvFromSource{
			SecretRef: &corev1.SecretEnvSource{
				LocalObjectReference: corev1.LocalObjectReference{Name: b.Authentik.ConfigSecretName()},
			},
		})
	}
	envFrom = append(envFrom, slices.Concat(global.EnvFrom, c.spec.EnvFrom)...)

	resources := corev1.ResourceRequirements{}
	if c.spec.Resources != nil {
		resources = *c.spec.Resources
	}

	return &corev1.Container{
		Name:            c.name,
		Image:           b.Authentik.ImageRef(b.Version),
		ImagePullPolicy: b.pullPolicy(c),
		Args:            []string{c.arg},
		Env:             nilIfEmptySlice(env),
		EnvFrom:         nilIfEmptySlice(envFrom),
		Ports:           c.ports,
		VolumeMounts:    nilIfEmptySlice(b.volumeMounts(c)),
		LivenessProbe:   cmp.Or(c.spec.LivenessProbe, c.liveness),
		ReadinessProbe:  cmp.Or(c.spec.ReadinessProbe, c.readiness),
		StartupProbe:    cmp.Or(c.spec.StartupProbe, c.startup),
		Resources:       resources,
		SecurityContext: c.spec.ContainerSecurityContext,
		Lifecycle:       c.spec.Lifecycle,
	}
}

// geoipSidecar builds the geoipupdate container, or nil when GeoIP is off.
func (b *Builder) geoipSidecar() *corev1.Container {
	geoip := b.Authentik.Spec.GeoIP
	if geoip == nil || !geoip.Enabled {
		return nil
	}

	repository, tag, digest, pullPolicy := defaultGeoIPRepository, defaultGeoIPTag, "", corev1.PullPolicy(defaultPullPolicy)
	if geoip.Image != nil {
		repository = cmp.Or(geoip.Image.Repository, repository)
		tag = cmp.Or(geoip.Image.Tag, tag)
		digest = geoip.Image.Digest
		pullPolicy = cmp.Or(geoip.Image.PullPolicy, pullPolicy)
	}
	image := fmt.Sprintf("%s:%s", repository, tag)
	if digest != "" {
		image = fmt.Sprintf("%s@%s", image, digest)
	}

	accountKey, licenseKey := "GEOIPUPDATE_ACCOUNT_ID", "GEOIPUPDATE_LICENSE_KEY"
	secretName := b.Authentik.Fullname()
	if existing := geoip.ExistingSecret; existing != nil && existing.SecretName != "" {
		secretName = existing.SecretName
		accountKey = cmp.Or(existing.AccountID, "account_id")
		licenseKey = cmp.Or(existing.LicenseKey, "license_key")
	}

	env := slices.Clone(geoip.Env)
	env = append(env,
		corev1.EnvVar{Name: "GEOIPUPDATE_FREQUENCY", Value: fmt.Sprint(ptr.Deref(geoip.UpdateInterval, defaultGeoIPUpdateInterval))},
		corev1.EnvVar{Name: "GEOIPUPDATE_PRESERVE_FILE_TIMES", Value: "1"},
		corev1.EnvVar{Name: "GEOIPUPDATE_ACCOUNT_ID", ValueFrom: secretKeyRef(secretName, accountKey)},
		corev1.EnvVar{Name: "GEOIPUPDATE_LICENSE_KEY", ValueFrom: secretKeyRef(secretName, licenseKey)},
		corev1.EnvVar{Name: "GEOIPUPDATE_EDITION_IDS", Value: cmp.Or(geoip.EditionIDs, defaultGeoIPEditionIDs)},
	)

	resources := corev1.ResourceRequirements{}
	if geoip.Resources != nil {
		resources = *geoip.Resources
	}

	return &corev1.Container{
		Name:            "geoip",
		Image:           image,
		ImagePullPolicy: pullPolicy,
		Env:             env,
		EnvFrom:         nilIfEmptySlice(geoip.EnvFrom),
		VolumeMounts: append(slices.Clone(geoip.VolumeMounts),
			corev1.VolumeMount{Name: geoipVolumeName, MountPath: geoipDownloadPath}),
		Resources:       resources,
		SecurityContext: geoip.ContainerSecurityContext,
	}
}

func (b *Builder) volumeMounts(c *component) []corev1.VolumeMount {
	global := b.global()
	mounts := slices.Concat(global.VolumeMounts, c.spec.VolumeMounts)

	if geoip := b.Authentik.Spec.GeoIP; geoip != nil && geoip.Enabled {
		mounts = append(mounts, corev1.VolumeMount{Name: geoipVolumeName, MountPath: geoipMountPath})
	}

	if c.mountsBlueprints {
		if blueprints := b.Authentik.Spec.Blueprints; blueprints != nil {
			for _, name := range blueprints.ConfigMaps {
				mounts = append(mounts, corev1.VolumeMount{
					Name:      blueprintConfigMapPrefix + name,
					MountPath: blueprintMountPrefix + "cm-" + name,
				})
			}
			for _, name := range blueprints.Secrets {
				mounts = append(mounts, corev1.VolumeMount{
					Name:      blueprintSecretPrefix + name,
					MountPath: blueprintMountPrefix + "secret-" + name,
				})
			}
		}
	}

	return mounts
}

func (b *Builder) volumes(c *component) []corev1.Volume {
	global := b.global()
	volumes := slices.Concat(global.Volumes, c.spec.Volumes)

	if geoip := b.Authentik.Spec.GeoIP; geoip != nil && geoip.Enabled {
		volumes = append(volumes, corev1.Volume{
			Name:         geoipVolumeName,
			VolumeSource: corev1.VolumeSource{EmptyDir: &corev1.EmptyDirVolumeSource{}},
		})
	}

	if c.mountsBlueprints {
		if blueprints := b.Authentik.Spec.Blueprints; blueprints != nil {
			for _, name := range blueprints.ConfigMaps {
				volumes = append(volumes, corev1.Volume{
					Name: blueprintConfigMapPrefix + name,
					VolumeSource: corev1.VolumeSource{
						ConfigMap: &corev1.ConfigMapVolumeSource{
							LocalObjectReference: corev1.LocalObjectReference{Name: name},
						},
					},
				})
			}
			for _, name := range blueprints.Secrets {
				volumes = append(volumes, corev1.Volume{
					Name: blueprintSecretPrefix + name,
					VolumeSource: corev1.VolumeSource{
						Secret: &corev1.SecretVolumeSource{SecretName: name},
					},
				})
			}
		}
	}

	return nilIfEmptySlice(volumes)
}

// strategy layers the component's rollout settings over the global ones.
func (b *Builder) strategy(c *component) (appsv1.DeploymentStrategy, error) {
	merged, err := mergeStructs(b.global().DeploymentStrategy, c.spec.DeploymentStrategy)
	if err != nil || merged == nil {
		return appsv1.DeploymentStrategy{}, err
	}

	switch merged.Type {
	case "Recreate":
		// Recreate has no tunables, and the API server rejects rollingUpdate
		// alongside it even if the merge carried one over.
		return appsv1.DeploymentStrategy{Type: appsv1.RecreateDeploymentStrategyType}, nil
	case "RollingUpdate":
		strategy := appsv1.DeploymentStrategy{Type: appsv1.RollingUpdateDeploymentStrategyType}
		if merged.RollingUpdate != nil {
			strategy.RollingUpdate = &appsv1.RollingUpdateDeployment{
				MaxSurge:       merged.RollingUpdate.MaxSurge,
				MaxUnavailable: merged.RollingUpdate.MaxUnavailable,
			}
		}
		return strategy, nil
	default:
		return appsv1.DeploymentStrategy{}, nil
	}
}

// affinity returns the component's own affinity, or the rules generated from
// the global preset.
func (b *Builder) affinity(c *component) *corev1.Affinity {
	if c.spec.Affinity != nil {
		return c.spec.Affinity
	}

	preset := b.Authentik.Spec.Global.GetAffinity()
	selector := &metav1.LabelSelector{MatchLabels: b.SelectorLabels(c.name)}
	affinity := &corev1.Affinity{}

	switch preset.PodAntiAffinity {
	case "soft":
		affinity.PodAntiAffinity = &corev1.PodAntiAffinity{
			PreferredDuringSchedulingIgnoredDuringExecution: []corev1.WeightedPodAffinityTerm{{
				Weight: 100,
				PodAffinityTerm: corev1.PodAffinityTerm{
					LabelSelector: selector,
					TopologyKey:   corev1.LabelHostname,
				},
			}},
		}
	case "hard":
		affinity.PodAntiAffinity = &corev1.PodAntiAffinity{
			PreferredDuringSchedulingIgnoredDuringExecution: []corev1.WeightedPodAffinityTerm{{
				Weight: 100,
				PodAffinityTerm: corev1.PodAffinityTerm{
					LabelSelector: selector,
					TopologyKey:   corev1.LabelTopologyZone,
				},
			}},
			RequiredDuringSchedulingIgnoredDuringExecution: []corev1.PodAffinityTerm{{
				LabelSelector: selector,
				TopologyKey:   corev1.LabelHostname,
			}},
		}
	}

	if node := preset.NodeAffinity; node != nil && len(node.MatchExpressions) > 0 {
		switch node.Type {
		case "soft":
			affinity.NodeAffinity = &corev1.NodeAffinity{
				PreferredDuringSchedulingIgnoredDuringExecution: []corev1.PreferredSchedulingTerm{{
					Weight:     1,
					Preference: corev1.NodeSelectorTerm{MatchExpressions: node.MatchExpressions},
				}},
			}
		case "hard":
			affinity.NodeAffinity = &corev1.NodeAffinity{
				RequiredDuringSchedulingIgnoredDuringExecution: &corev1.NodeSelector{
					NodeSelectorTerms: []corev1.NodeSelectorTerm{{MatchExpressions: node.MatchExpressions}},
				},
			}
		}
	}

	if affinity.PodAntiAffinity == nil && affinity.NodeAffinity == nil {
		return nil
	}
	return affinity
}

// topologySpreadConstraints defaults each constraint's selector to this
// component's pods, which is what makes an otherwise incomplete constraint
// usable.
func (b *Builder) topologySpreadConstraints(c *component) []corev1.TopologySpreadConstraint {
	constraints := firstNonEmpty(c.spec.TopologySpreadConstraints, b.global().TopologySpreadConstraints)
	if len(constraints) == 0 {
		return nil
	}

	out := slices.Clone(constraints)
	for i := range out {
		if out[i].LabelSelector == nil {
			out[i].LabelSelector = &metav1.LabelSelector{MatchLabels: b.SelectorLabels(c.name)}
		}
	}
	return out
}

// serviceAccountFor picks the ServiceAccount a component runs as. Only the
// worker needs one by default, because only it talks to the Kubernetes API.
func (b *Builder) serviceAccountFor(c *component) string {
	if c.spec.ServiceAccountName != "" {
		return c.spec.ServiceAccountName
	}
	if c.managesOutposts && b.serviceAccountEnabled() {
		return b.ServiceAccountName()
	}
	return ""
}

func (b *Builder) pullPolicy(c *component) corev1.PullPolicy {
	if c.spec.Image != nil && c.spec.Image.PullPolicy != "" {
		return c.spec.Image.PullPolicy
	}
	if image := b.global().Image; image != nil && image.PullPolicy != "" {
		return image.PullPolicy
	}
	return defaultPullPolicy
}

func (b *Builder) configSecretMounted() bool {
	config := b.Authentik.Spec.Authentik
	if config == nil {
		return true
	}
	if config.ExistingSecret != nil && config.ExistingSecret.SecretName != "" {
		return true
	}
	return config.Enabled == nil || *config.Enabled
}

// configChecksum fingerprints the configuration Secret's contents. Empty when
// the operator does not render one, since it cannot then see the contents.
func (b *Builder) configChecksum() (string, error) {
	secret, err := b.ConfigSecret()
	if err != nil || secret == nil {
		return "", err
	}

	// Map iteration order is random, so the keys have to be sorted or the
	// checksum would change on every reconcile and restart the pods.
	digest := sha256.New()
	for _, key := range slices.Sorted(maps.Keys(secret.Data)) {
		digest.Write([]byte(key))
		digest.Write([]byte{0})
		digest.Write(secret.Data[key])
		digest.Write([]byte{0})
	}
	return hex.EncodeToString(digest.Sum(nil)), nil
}

// webPath is the path authentik is served under; the health endpoints hang
// off it.
func (b *Builder) webPath() string {
	if config := b.Authentik.Spec.Authentik; config != nil && config.Web != nil && config.Web.Path != "" {
		return config.Web.Path
	}
	return defaultWebPath
}

func (b *Builder) global() *akv1alpha1.GlobalSpec {
	if g := b.Authentik.Spec.Global; g != nil {
		return g
	}
	return &akv1alpha1.GlobalSpec{}
}

func httpProbe(path string, failureThreshold, initialDelay int32) *corev1.Probe {
	return &corev1.Probe{
		ProbeHandler: corev1.ProbeHandler{
			HTTPGet: &corev1.HTTPGetAction{Path: path, Port: intstr.FromString("http")},
		},
		FailureThreshold:    failureThreshold,
		InitialDelaySeconds: initialDelay,
		PeriodSeconds:       defaultProbePeriod,
		SuccessThreshold:    defaultProbeSuccessThreshold,
		TimeoutSeconds:      defaultProbeTimeout,
	}
}

func execProbe(failureThreshold, initialDelay int32) *corev1.Probe {
	return &corev1.Probe{
		ProbeHandler: corev1.ProbeHandler{
			Exec: &corev1.ExecAction{Command: []string{"ak", "healthcheck"}},
		},
		FailureThreshold:    failureThreshold,
		InitialDelaySeconds: initialDelay,
		PeriodSeconds:       defaultProbePeriod,
		SuccessThreshold:    defaultProbeSuccessThreshold,
		TimeoutSeconds:      defaultProbeTimeout,
	}
}

func secretKeyRef(name, key string) *corev1.EnvVarSource {
	return &corev1.EnvVarSource{
		SecretKeyRef: &corev1.SecretKeySelector{
			LocalObjectReference: corev1.LocalObjectReference{Name: name},
			Key:                  key,
		},
	}
}

// mergeStructs deep-merges override onto base through JSON, so a partial
// override keeps the fields it does not mention.
func mergeStructs[T any](base, override *T) (*T, error) {
	if base == nil {
		return override, nil
	}
	if override == nil {
		return base, nil
	}

	// Decoding each in turn onto a fresh value is the merge: a field the
	// override does not mention keeps the base's value. The base is copied
	// through JSON as well, so merging cannot reach into its nested pointers.
	merged := new(T)
	for _, value := range []*T{base, override} {
		encoded, err := json.Marshal(value)
		if err != nil {
			return nil, fmt.Errorf("failed to encode for merging: %w", err)
		}
		if err := json.Unmarshal(encoded, merged); err != nil {
			return nil, fmt.Errorf("failed to decode for merging: %w", err)
		}
	}
	return merged, nil
}

func firstNonEmpty[T any](value, fallback []T) []T {
	if len(value) > 0 {
		return value
	}
	return fallback
}

func nilIfEmptySlice[T any](value []T) []T {
	if len(value) == 0 {
		return nil
	}
	return value
}
