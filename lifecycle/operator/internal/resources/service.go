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
	"fmt"
	"strconv"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/util/intstr"

	akv1alpha1 "goauthentik.io/lifecycle/operator/api/v1alpha1"
)

// ServerService is the Service routing traffic to the authentik server.
func (b *Builder) ServerService(c *component) *corev1.Service {
	spec := &akv1alpha1.ServerServiceSpec{}
	if s := b.Authentik.Spec.Server; s != nil && s.Service != nil {
		spec = s.Service
	}

	serviceType := corev1.ServiceType(firstNonZero(string(spec.Type), defaultServiceType))

	httpPort := corev1.ServicePort{
		Name:       firstNonZero(spec.ServicePortHTTPName, defaultServicePortHTTPName),
		Protocol:   corev1.ProtocolTCP,
		Port:       valueOr(spec.ServicePortHTTP, defaultServicePortHTTP),
		TargetPort: intstr.FromInt32(b.containerPort(c, "http")),
	}
	httpsPort := corev1.ServicePort{
		Name:       firstNonZero(spec.ServicePortHTTPSName, defaultServicePortHTTPSName),
		Protocol:   corev1.ProtocolTCP,
		Port:       valueOr(spec.ServicePortHTTPS, defaultServicePortHTTPS),
		TargetPort: intstr.FromInt32(b.containerPort(c, "https")),
	}

	if serviceType == corev1.ServiceTypeNodePort {
		httpPort.NodePort = valueOr(spec.NodePortHTTP, defaultNodePortHTTP)
		httpsPort.NodePort = valueOr(spec.NodePortHTTPS, defaultNodePortHTTPS)
	}
	if spec.ServicePortHTTPAppProtocol != "" {
		httpPort.AppProtocol = ptr(spec.ServicePortHTTPAppProtocol)
	}
	if spec.ServicePortHTTPSAppProtocol != "" {
		httpsPort.AppProtocol = ptr(spec.ServicePortHTTPSAppProtocol)
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

// MetricsService exposes a component's metrics port, or nil when metrics are
// off.
func (b *Builder) MetricsService(c *component) *corev1.Service {
	metrics := c.spec.Metrics
	if metrics == nil || !metrics.Enabled {
		return nil
	}

	spec := &akv1alpha1.MetricsServiceSpec{}
	if metrics.Service != nil {
		spec = metrics.Service
	}

	port := valueOr(spec.ServicePort, defaultMetricsServicePort)
	annotations := spec.Annotations
	if g := b.Authentik.Spec.Global; g != nil && g.AddPrometheusAnnotations != nil && *g.AddPrometheusAnnotations {
		// An alternative to a ServiceMonitor, for clusters without the
		// Prometheus Operator.
		annotations = mergedMap(map[string]string{
			"prometheus.io/port":   strconv.Itoa(int(port)),
			"prometheus.io/scrape": "true",
		}, annotations)
	}

	serviceType := corev1.ServiceType(firstNonZero(string(spec.Type), defaultServiceType))
	service := &corev1.Service{
		ObjectMeta: b.objectMeta(b.metricsName(c), c.name+"-metrics", spec.Labels, annotations),
		Spec: corev1.ServiceSpec{
			Type: serviceType,
			Ports: []corev1.ServicePort{{
				Name:       firstNonZero(spec.PortName, defaultMetricsPortName),
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

// metricsName is the name of a component's metrics Service.
func (b *Builder) metricsName(c *component) string {
	return truncate63(fmt.Sprintf("%s-metrics", c.objectName))
}

// containerPort looks up a named port on the component's container.
func (b *Builder) containerPort(c *component, name string) int32 {
	for _, port := range c.ports {
		if port.Name == name {
			return port.ContainerPort
		}
	}
	return 0
}
