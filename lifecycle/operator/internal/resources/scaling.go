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
	autoscalingv2 "k8s.io/api/autoscaling/v2"
	corev1 "k8s.io/api/core/v1"
	policyv1 "k8s.io/api/policy/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
)

// HorizontalPodAutoscaler scales a component, or nil when autoscaling is off.
func (b *Builder) HorizontalPodAutoscaler(c *component) *autoscalingv2.HorizontalPodAutoscaler {
	spec := c.spec.Autoscaling
	if spec == nil || !spec.Enabled {
		return nil
	}

	metrics := spec.Metrics
	if len(metrics) == 0 {
		// The chart emits memory before CPU; the order is not significant to
		// the autoscaler but keeping it avoids a needless diff on adoption.
		if spec.TargetMemoryUtilizationPercentage != nil {
			metrics = append(metrics, utilizationMetric(corev1.ResourceMemory, *spec.TargetMemoryUtilizationPercentage))
		}
		if spec.TargetCPUUtilizationPercentage != nil {
			metrics = append(metrics, utilizationMetric(corev1.ResourceCPU, *spec.TargetCPUUtilizationPercentage))
		}
	}

	return &autoscalingv2.HorizontalPodAutoscaler{
		ObjectMeta: b.objectMeta(c.objectName, c.name, nil, spec.Annotations),
		Spec: autoscalingv2.HorizontalPodAutoscalerSpec{
			ScaleTargetRef: autoscalingv2.CrossVersionObjectReference{
				APIVersion: "apps/v1",
				Kind:       "Deployment",
				Name:       c.objectName,
			},
			MinReplicas: spec.MinReplicas,
			MaxReplicas: valueOr(spec.MaxReplicas, 5),
			Metrics:     metrics,
			Behavior:    spec.Behavior,
		},
	}
}

func utilizationMetric(name corev1.ResourceName, target int32) autoscalingv2.MetricSpec {
	return autoscalingv2.MetricSpec{
		Type: autoscalingv2.ResourceMetricSourceType,
		Resource: &autoscalingv2.ResourceMetricSource{
			Name: name,
			Target: autoscalingv2.MetricTarget{
				Type:               autoscalingv2.UtilizationMetricType,
				AverageUtilization: ptr(target),
			},
		},
	}
}

// PodDisruptionBudget protects a component during voluntary disruption, or nil
// when disabled.
func (b *Builder) PodDisruptionBudget(c *component) *policyv1.PodDisruptionBudget {
	spec := c.spec.PDB
	if spec == nil || !spec.Enabled {
		return nil
	}

	pdb := &policyv1.PodDisruptionBudget{
		ObjectMeta: b.objectMeta(c.objectName, c.name, spec.Labels, spec.Annotations),
		Spec: policyv1.PodDisruptionBudgetSpec{
			Selector: &metav1.LabelSelector{MatchLabels: b.SelectorLabels(c.name)},
		},
	}

	// The two bounds are mutually exclusive; maxUnavailable wins, matching the
	// chart. Neither set means minAvailable 0, which permits any eviction.
	switch {
	case spec.MaxUnavailable != nil:
		pdb.Spec.MaxUnavailable = spec.MaxUnavailable
	case spec.MinAvailable != nil:
		pdb.Spec.MinAvailable = spec.MinAvailable
	default:
		pdb.Spec.MinAvailable = ptr(intstr.FromInt32(0))
	}

	return pdb
}
