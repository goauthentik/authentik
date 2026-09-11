package resources

import (
	"cmp"
	"strconv"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/utils/ptr"

	akv1alpha1 "goauthentik.io/lifecycle/operator/api/v1alpha1"
)

// ServerService is the Service routing traffic to the authentik server.
func (b *Builder) ServerService(c *component) *corev1.Service {
	spec := &akv1alpha1.ServerServiceSpec{}
	if s := b.Authentik.Spec.Server; s != nil && s.Service != nil {
		spec = s.Service
	}

	serviceType := corev1.ServiceType(cmp.Or(string(spec.Type), defaultServiceType))

	httpPort := corev1.ServicePort{
		Name:       cmp.Or(spec.ServicePortHTTPName, defaultServicePortHTTPName),
		Protocol:   corev1.ProtocolTCP,
		Port:       ptr.Deref(spec.ServicePortHTTP, defaultServicePortHTTP),
		TargetPort: intstr.FromInt32(b.containerPort(c, "http")),
	}
	httpsPort := corev1.ServicePort{
		Name:       cmp.Or(spec.ServicePortHTTPSName, defaultServicePortHTTPSName),
		Protocol:   corev1.ProtocolTCP,
		Port:       ptr.Deref(spec.ServicePortHTTPS, defaultServicePortHTTPS),
		TargetPort: intstr.FromInt32(b.containerPort(c, "https")),
	}

	if serviceType == corev1.ServiceTypeNodePort {
		httpPort.NodePort = ptr.Deref(spec.NodePortHTTP, defaultNodePortHTTP)
		httpsPort.NodePort = ptr.Deref(spec.NodePortHTTPS, defaultNodePortHTTPS)
	}
	if spec.ServicePortHTTPAppProtocol != "" {
		httpPort.AppProtocol = new(spec.ServicePortHTTPAppProtocol)
	}
	if spec.ServicePortHTTPSAppProtocol != "" {
		httpsPort.AppProtocol = new(spec.ServicePortHTTPSAppProtocol)
	}

	service := &corev1.Service{
		ObjectMeta: b.objectMeta(b.ServerName(), c.name, spec.Labels, spec.Annotations),
		Spec: corev1.ServiceSpec{
			Type:                  serviceType,
			Ports:                 []corev1.ServicePort{httpPort, httpsPort},
			Selector:              b.SelectorLabels(c.name),
			ExternalIPs:           spec.ExternalIPs,
			ExternalTrafficPolicy: spec.ExternalTrafficPolicy,
			SessionAffinity:       spec.SessionAffinity,
			SessionAffinityConfig: spec.SessionAffinityConfig,
		},
	}

	if spec.PublishNotReadyAddresses != nil {
		service.Spec.PublishNotReadyAddresses = *spec.PublishNotReadyAddresses
	}

	// These fields are only meaningful for their own Service type, and the API
	// server rejects some of them outright on the wrong one.
	switch serviceType {
	case corev1.ServiceTypeLoadBalancer:
		service.Spec.LoadBalancerIP = spec.LoadBalancerIP
		service.Spec.LoadBalancerSourceRanges = spec.LoadBalancerSourceRanges
	case corev1.ServiceTypeClusterIP:
		service.Spec.ClusterIP = spec.ClusterIP
	}

	return service
}

// MetricsService exposes a component's metrics port, or nil when metrics are off.
func (b *Builder) MetricsService(c *component) *corev1.Service {
	metrics := c.spec.Metrics
	if metrics == nil || !metrics.Enabled {
		return nil
	}

	spec := &akv1alpha1.MetricsServiceSpec{}
	if metrics.Service != nil {
		spec = metrics.Service
	}

	port := ptr.Deref(spec.ServicePort, defaultMetricsServicePort)
	annotations := spec.Annotations
	if g := b.Authentik.Spec.Global; g != nil && g.AddPrometheusAnnotations != nil && *g.AddPrometheusAnnotations {
		// An alternative to a ServiceMonitor, for clusters without the
		// Prometheus Operator.
		annotations = mergedMap(map[string]string{
			"prometheus.io/port":   strconv.Itoa(int(port)),
			"prometheus.io/scrape": "true",
		}, annotations)
	}

	serviceType := corev1.ServiceType(cmp.Or(string(spec.Type), defaultServiceType))
	service := &corev1.Service{
		ObjectMeta: b.objectMeta(akv1alpha1.TruncateName(c.objectName+"-metrics"),
			c.name+"-metrics", spec.Labels, annotations),
		Spec: corev1.ServiceSpec{
			Type: serviceType,
			Ports: []corev1.ServicePort{{
				Name:       cmp.Or(spec.PortName, defaultMetricsPortName),
				Protocol:   corev1.ProtocolTCP,
				Port:       port,
				TargetPort: intstr.FromString(defaultMetricsPortName),
			}},
			// Selects the component's pods, not the metrics component label,
			// which exists only to distinguish this Service from the main one.
			Selector: b.SelectorLabels(c.name),
		},
	}

	if serviceType == corev1.ServiceTypeClusterIP {
		service.Spec.ClusterIP = spec.ClusterIP
	}

	return service
}

func (b *Builder) containerPort(c *component, name string) int32 {
	for _, port := range c.ports {
		if port.Name == name {
			return port.ContainerPort
		}
	}
	return 0
}
