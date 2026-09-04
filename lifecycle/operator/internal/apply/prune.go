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

package apply

import (
	"context"
	"fmt"

	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
)

// rbacGroup is the API group the RBAC kinds live in.
const rbacGroup = "rbac.authorization.k8s.io"

// prunableKinds are the kinds the operator will delete when they carry its
// labels but are no longer in the desired set.
//
// This is an explicit list rather than everything discoverable, because pruning
// deletes data. A kind absent from this list is simply never pruned: turning off
// a feature leaves its object behind, which is recoverable. The opposite
// mistake -- pruning a kind the operator does not really manage -- is not.
//
// Jobs are deliberately absent. The migration Jobs are the operator's own but
// are meant to outlive a reconcile, so their owner reference and TTL clean them
// up instead.
var prunableKinds = []schema.GroupVersionKind{
	{Group: "", Version: "v1", Kind: "Secret"},
	{Group: "", Version: "v1", Kind: "Service"},
	{Group: "", Version: "v1", Kind: "ServiceAccount"},
	{Group: "", Version: "v1", Kind: "ConfigMap"},
	{Group: "apps", Version: "v1", Kind: "Deployment"},
	{Group: "apps", Version: "v1", Kind: "StatefulSet"},
	{Group: "networking.k8s.io", Version: "v1", Kind: "Ingress"},
	{Group: "autoscaling", Version: "v2", Kind: "HorizontalPodAutoscaler"},
	{Group: "policy", Version: "v1", Kind: "PodDisruptionBudget"},
	{Group: rbacGroup, Version: "v1", Kind: "Role"},
	{Group: rbacGroup, Version: "v1", Kind: "RoleBinding"},
	{Group: rbacGroup, Version: "v1", Kind: "ClusterRole"},
	{Group: rbacGroup, Version: "v1", Kind: "ClusterRoleBinding"},
	{Group: "monitoring.coreos.com", Version: "v1", Kind: "ServiceMonitor"},
	{Group: "monitoring.coreos.com", Version: "v1", Kind: "PrometheusRule"},
	{Group: "gateway.networking.k8s.io", Version: "v1", Kind: "HTTPRoute"},
}

// Prune deletes objects carrying the given labels that are not in keep.
//
// The label selector is what bounds the damage: it only ever considers objects
// this operator labelled for this specific Authentik resource.
func (a *Applier) Prune(
	ctx context.Context,
	namespace string,
	selector map[string]string,
	keep []ObjectKey,
) ([]ObjectKey, error) {
	log := logf.FromContext(ctx)

	if len(selector) == 0 {
		// Without a selector this would list every object of every prunable
		// kind and delete it. Refuse rather than risk that.
		return nil, fmt.Errorf("refusing to prune without a label selector")
	}

	wanted := make(map[string]struct{}, len(keep))
	for _, key := range keep {
		wanted[key.String()] = struct{}{}
	}

	pruned := []ObjectKey{}
	for _, gvk := range prunableKinds {
		found, err := a.listManaged(ctx, gvk, namespace, selector)
		if err != nil {
			return pruned, err
		}

		for _, object := range found {
			key := ObjectKey{
				GroupVersionKind: gvk,
				Namespace:        object.GetNamespace(),
				Name:             object.GetName(),
			}
			if _, ok := wanted[key.String()]; ok {
				continue
			}
			// Something else is already deleting it; deleting again would only
			// race with the garbage collector.
			if object.GetDeletionTimestamp() != nil {
				continue
			}

			log.Info("Pruning an object that is no longer part of the desired state", "object", key.String())
			if err := a.Client.Delete(ctx, &object); err != nil && !apierrors.IsNotFound(err) {
				return pruned, fmt.Errorf("failed to prune %s: %w", key, err)
			}
			pruned = append(pruned, key)
		}
	}

	return pruned, nil
}

// listManaged returns the operator's objects of one kind.
func (a *Applier) listManaged(
	ctx context.Context,
	gvk schema.GroupVersionKind,
	namespace string,
	selector map[string]string,
) ([]unstructured.Unstructured, error) {
	list := &unstructured.UnstructuredList{}
	list.SetGroupVersionKind(schema.GroupVersionKind{
		Group:   gvk.Group,
		Version: gvk.Version,
		Kind:    gvk.Kind + "List",
	})

	options := []client.ListOption{client.MatchingLabels(selector)}
	// Cluster-scoped kinds have no namespace to scope the list to.
	if !isClusterScoped(gvk) {
		options = append(options, client.InNamespace(namespace))
	}

	if err := a.Client.List(ctx, list, options...); err != nil {
		// An optional CRD that is not installed has nothing to prune.
		if isMissingKind(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to list %s: %w", gvk.Kind, err)
	}

	return list.Items, nil
}

// isClusterScoped reports whether a kind lives outside a namespace.
func isClusterScoped(gvk schema.GroupVersionKind) bool {
	switch gvk.Kind {
	case "ClusterRole", "ClusterRoleBinding":
		return true
	default:
		return false
	}
}

// DeleteClusterScoped removes the cluster-scoped objects belonging to an
// instance.
//
// These have no owner reference -- a namespaced resource cannot own a
// cluster-scoped one -- so nothing would otherwise delete them when the
// Authentik resource goes away.
func (a *Applier) DeleteClusterScoped(ctx context.Context, selector map[string]string) error {
	if len(selector) == 0 {
		return fmt.Errorf("refusing to delete cluster-scoped objects without a label selector")
	}
	log := logf.FromContext(ctx)

	for _, gvk := range prunableKinds {
		if !isClusterScoped(gvk) {
			continue
		}

		found, err := a.listManaged(ctx, gvk, "", selector)
		if err != nil {
			return err
		}

		for _, object := range found {
			log.Info("Deleting a cluster-scoped object", "kind", gvk.Kind, "name", object.GetName())
			if err := a.Client.Delete(ctx, &object); err != nil && !apierrors.IsNotFound(err) {
				return fmt.Errorf("failed to delete %s %q: %w", gvk.Kind, object.GetName(), err)
			}
		}
	}

	return nil
}
