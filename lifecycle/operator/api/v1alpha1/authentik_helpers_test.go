package v1alpha1

import (
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

func authentik(name, namespace string, spec AuthentikSpec) *Authentik {
	return &Authentik{
		Name: name, Namespace: namespace,
		Spec: spec,
	}
}

var _ = Describe("Naming", func() {
	It("mirrors the chart's fullname template when the release name already contains the chart name", func() {
		// `helm install authentik ./authentik` produces objects named
		// "authentik-server", not "authentik-authentik-server".
		ak := authentik("authentik", "authentik", AuthentikSpec{})
		Expect(ak.Fullname()).To(Equal("authentik"))
		Expect(ak.ComponentFullname(ak.ServerComponentName())).To(Equal("authentik-server"))
		Expect(ak.ComponentFullname(ak.WorkerComponentName())).To(Equal("authentik-worker"))
	})

	It("prefixes the chart name when the release name does not contain it", func() {
		ak := authentik("sso", "authentik", AuthentikSpec{})
		Expect(ak.Fullname()).To(Equal("sso-authentik"))
		Expect(ak.ComponentFullname("server")).To(Equal("sso-authentik-server"))
	})

	It("honours an explicit release name over the object name", func() {
		ak := authentik("my-authentik-cr", DefaultName, AuthentikSpec{ReleaseName: DefaultName})
		Expect(ak.ReleaseName()).To(Equal("authentik"))
		Expect(ak.Fullname()).To(Equal("authentik"))
	})

	It("lets global.fullnameOverride win over fullnameOverride", func() {
		ak := authentik("authentik", "authentik", AuthentikSpec{
			FullnameOverride: "ignored",
			Global:           &GlobalSpec{FullnameOverride: "wins"},
		})
		Expect(ak.Fullname()).To(Equal("wins"))
	})

	It("lets global.nameOverride win over nameOverride", func() {
		ak := authentik("release", "authentik", AuthentikSpec{
			NameOverride: "ignored",
			Global:       &GlobalSpec{NameOverride: "idp"},
		})
		Expect(ak.BaseName()).To(Equal("idp"))
		Expect(ak.Fullname()).To(Equal("release-idp"))
	})

	It("truncates to the 63 character DNS label limit and trims a trailing dash", func() {
		ak := authentik("a-very-long-release-name-that-goes-well-past-the-limit-imposed-by-dns", "authentik", AuthentikSpec{})
		Expect(len(ak.Fullname())).To(BeNumerically("<=", 63))
		Expect(ak.Fullname()).ToNot(HaveSuffix("-"))
	})

	It("resolves the configuration Secret name, preferring an existing Secret", func() {
		ak := authentik("authentik", "authentik", AuthentikSpec{})
		Expect(ak.ConfigSecretName()).To(Equal("authentik"))

		ak.Spec.Authentik = &AuthentikConfigSpec{
			ExistingSecret: &AuthentikExistingSecret{SecretName: "authentik-config"},
		}
		Expect(ak.ConfigSecretName()).To(Equal("authentik-config"))
	})
})

var _ = Describe("Defaults", func() {
	It("prunes objects that leave the desired state unless explicitly disabled", func() {
		Expect(authentik("a", "n", AuthentikSpec{}).PruneEnabled()).To(BeTrue())
		Expect(authentik("a", "n", AuthentikSpec{Prune: new(false)}).PruneEnabled()).To(BeFalse())
	})

	It("scopes the owner selector to one instance, so two cannot prune each other", func() {
		first := authentik("one", "authentik", AuthentikSpec{}).OwnerSelector()
		second := authentik("two", "authentik", AuthentikSpec{}).OwnerSelector()

		Expect(first).To(HaveKeyWithValue(ManagedByLabel, ManagedByLabelValue))
		Expect(first[InstanceOwnerLabel]).ToNot(Equal(second[InstanceOwnerLabel]))
	})

	It("gates upgrades behind migrations unless explicitly disabled", func() {
		Expect(authentik("a", "n", AuthentikSpec{}).MigrationsEnabled()).To(BeTrue())
		Expect(authentik("a", "n", AuthentikSpec{Migrations: &MigrationsSpec{}}).MigrationsEnabled()).To(BeTrue())
		Expect(authentik("a", "n", AuthentikSpec{
			Migrations: &MigrationsSpec{Enabled: new(false)},
		}).MigrationsEnabled()).To(BeFalse())
	})

	It("only auto-updates when a branch is given", func() {
		Expect(authentik("a", "n", AuthentikSpec{}).AutoUpdateEnabled()).To(BeFalse())
		Expect(authentik("a", "n", AuthentikSpec{
			AutoUpdate: &AutoUpdateSpec{Enabled: true},
		}).AutoUpdateEnabled()).To(BeFalse(), "enabled without a branch is not actionable")
		Expect(authentik("a", "n", AuthentikSpec{
			AutoUpdate: &AutoUpdateSpec{Enabled: true, Branch: "main"},
		}).AutoUpdateEnabled()).To(BeTrue())
	})

	It("builds image references the same way the chart's templates do", func() {
		ak := authentik("a", "n", AuthentikSpec{})
		Expect(ak.ImageRef("2026.8.0")).To(Equal("ghcr.io/goauthentik/server:2026.8.0"))

		ak.Spec.Global = &GlobalSpec{Image: &ImageSpec{
			Repository: "registry.example.com/authentik",
			Digest:     "sha256:0000000000000000000000000000000000000000000000000000000000000000",
		}}
		Expect(ak.ImageRef("2026.8.0")).To(Equal(
			"registry.example.com/authentik:2026.8.0@sha256:0000000000000000000000000000000000000000000000000000000000000000"))
	})
})
