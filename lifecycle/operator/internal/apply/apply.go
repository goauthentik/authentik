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

// Package apply reconciles a set of desired objects into a cluster: it applies
// each one server-side and deletes the ones the operator used to manage but no
// longer wants.
package apply

import (
	"context"
	"errors"
	"fmt"

	apierrors "k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/client/apiutil"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
)

// FieldOwner identifies this operator to server-side apply.
//
// Every field the operator sets is recorded under this owner, which is what
// lets an apply remove a field it previously set, and what makes a conflict
// with another controller visible instead of silent.
const FieldOwner = client.FieldOwner("authentik-operator")

// Applier applies objects and prunes the ones no longer wanted.
type Applier struct {
	Client client.Client
	Scheme *runtime.Scheme
}

// ObjectKey identifies an applied object well enough to compare desired against
// existing.
type ObjectKey struct {
	GroupVersionKind schema.GroupVersionKind
	Namespace        string
	Name             string
}

func (k ObjectKey) String() string {
	if k.Namespace == "" {
		return fmt.Sprintf("%s/%s", k.GroupVersionKind.Kind, k.Name)
	}
	return fmt.Sprintf("%s/%s/%s", k.GroupVersionKind.Kind, k.Namespace, k.Name)
}

// Result reports what an Apply did.
type Result struct {
	// Applied are the objects that were sent to the API server.
	Applied []ObjectKey
	// Pruned are the objects that were deleted because they are no longer
	// wanted.
	Pruned []ObjectKey
	// Skipped are the objects whose kind the cluster does not know, which
	// happens when an optional CRD such as ServiceMonitor is not installed.
	Skipped []ObjectKey
}

// Apply reconciles the desired objects into the cluster.
//
// owner is set as the controller reference on every namespaced object in the
// same namespace as the owner, so those are garbage collected with it.
// Cluster-scoped objects and objects in another namespace cannot carry that
// reference and are cleaned up explicitly on delete.
func (a *Applier) Apply(ctx context.Context, owner client.Object, desired []client.Object) (*Result, error) {
	log := logf.FromContext(ctx)
	result := &Result{}

	for _, object := range desired {
		key, err := a.objectKey(object)
		if err != nil {
			return result, err
		}

		if a.canOwn(owner, object) {
			if err := ctrl.SetControllerReference(owner, object, a.Scheme); err != nil {
				return result, fmt.Errorf("failed to set the owner of %s: %w", key, err)
			}
		}

		if err := a.applyObject(ctx, object); err != nil {
			// A kind the cluster does not have is a configuration problem the
			// user can fix by installing the CRD, not a reason to fail the
			// whole reconcile and leave authentik un-deployed.
			if isMissingKind(err) {
				log.Info("Skipping an object whose kind is not installed in this cluster",
					"object", key.String(), "kind", key.GroupVersionKind.String())
				result.Skipped = append(result.Skipped, key)
				continue
			}
			return result, fmt.Errorf("failed to apply %s: %w", key, err)
		}

		result.Applied = append(result.Applied, key)
	}

	return result, nil
}

// applyObject sends one object through server-side apply.
func (a *Applier) applyObject(ctx context.Context, object client.Object) error {
	patch, err := a.forApply(object)
	if err != nil {
		return err
	}

	// ForceOwnership takes fields back from another field manager rather than
	// erroring. The operator is the source of truth for the fields it sets, so
	// a hand-edited Deployment is meant to be corrected, not to block reconciles.
	//
	// Client.Apply, which supersedes this patch type, only accepts a
	// runtime.ApplyConfiguration. Unstructured objects do not implement that
	// interface, and this operator has to apply them: ServiceMonitor,
	// PrometheusRule, HTTPRoute and everything in additionalObjects belong to
	// APIs it deliberately does not depend on.
	//nolint:staticcheck // see above; Client.Apply cannot express this
	return a.Client.Patch(ctx, patch, client.Apply, FieldOwner, client.ForceOwnership)
}

// forApply converts an object into the unstructured form to send.
//
// Typed objects are converted because marshalling them directly would include
// every zero-valued field that lacks omitempty -- creationTimestamp, an empty
// status, an empty resources block -- and server-side apply would record the
// operator as the owner of all of them.
func (a *Applier) forApply(object client.Object) (*unstructured.Unstructured, error) {
	if existing, ok := object.(*unstructured.Unstructured); ok {
		copied := existing.DeepCopy()
		unstructured.RemoveNestedField(copied.Object, "status")
		unstructured.RemoveNestedField(copied.Object, "metadata", "creationTimestamp")
		return copied, nil
	}

	gvk, err := apiutil.GVKForObject(object, a.Scheme)
	if err != nil {
		return nil, err
	}

	content, err := runtime.DefaultUnstructuredConverter.ToUnstructured(object)
	if err != nil {
		return nil, fmt.Errorf("failed to convert to unstructured: %w", err)
	}

	converted := &unstructured.Unstructured{Object: content}
	converted.SetGroupVersionKind(gvk)
	unstructured.RemoveNestedField(converted.Object, "status")
	unstructured.RemoveNestedField(converted.Object, "metadata", "creationTimestamp")
	// The converter emits these for the zero value of an embedded template's
	// metadata too, and they are not fields the operator means to own.
	unstructured.RemoveNestedField(converted.Object, "spec", "template", "metadata", "creationTimestamp")

	return converted, nil
}

// canOwn reports whether an owner reference from owner to object is valid.
func (a *Applier) canOwn(owner, object client.Object) bool {
	// Cluster-scoped objects cannot be owned by a namespaced resource, and a
	// cross-namespace owner reference is silently treated as a dangling one,
	// which makes the garbage collector delete the object.
	return object.GetNamespace() != "" && object.GetNamespace() == owner.GetNamespace()
}

// objectKey identifies an object for logging and comparison.
func (a *Applier) objectKey(object client.Object) (ObjectKey, error) {
	gvk, err := apiutil.GVKForObject(object, a.Scheme)
	if err != nil {
		return ObjectKey{}, err
	}
	return ObjectKey{
		GroupVersionKind: gvk,
		Namespace:        object.GetNamespace(),
		Name:             object.GetName(),
	}, nil
}

// isMissingKind reports whether an error means the cluster does not know the
// kind, as opposed to the object being invalid.
func isMissingKind(err error) bool {
	if meta.IsNoMatchError(err) {
		return true
	}
	if apierrors.IsNotFound(err) {
		// A NotFound on an apply means the API endpoint itself is absent, since
		// apply creates the object when it is missing.
		return true
	}
	var discoveryErr *meta.NoResourceMatchError
	return errors.As(err, &discoveryErr)
}
