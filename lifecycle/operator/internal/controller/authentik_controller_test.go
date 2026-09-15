package controller

import (
	"testing"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func TestWithoutDeploymentsDropsOnlyTheNamedDeployments(t *testing.T) {
	desired := []client.Object{
		&corev1.Secret{ObjectMeta: metav1.ObjectMeta{Name: "authentik"}},
		&appsv1.Deployment{ObjectMeta: metav1.ObjectMeta{Name: "authentik-server"}},
		&appsv1.Deployment{ObjectMeta: metav1.ObjectMeta{Name: "authentik-worker"}},
		// The server Service is named the same as the server Deployment; only
		// the Deployment should be dropped.
		&corev1.Service{ObjectMeta: metav1.ObjectMeta{Name: "authentik-server"}},
	}

	got := withoutDeployments(desired, "authentik-server", "authentik-worker")

	if len(got) != 2 {
		t.Fatalf("got %d objects, want 2: %+v", len(got), got)
	}
	for _, object := range got {
		if _, ok := object.(*appsv1.Deployment); ok {
			t.Errorf("a Deployment survived: %s", object.GetName())
		}
	}
	if got[0].GetName() != "authentik" || got[1].GetName() != "authentik-server" {
		t.Errorf("got = %+v, want the Secret and the Service, in order", got)
	}
}
