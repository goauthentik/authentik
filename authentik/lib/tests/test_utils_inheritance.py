"""Tests for inheritance helpers."""

from django.test import TestCase

from authentik.core.models import Provider
from authentik.core.tests.utils import create_test_flow
from authentik.lib.generators import generate_id
from authentik.lib.utils.inheritance import get_deepest_child
from authentik.providers.ldap.models import LDAPProvider
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.proxy.models import ProxyProvider


class TestInheritanceUtils(TestCase):
    """Tests for helper functions in authentik.lib.utils.inheritance."""

    def _get_provider_with_all_subclasses(self, provider_pk):
        qs = Provider.objects.all()
        for subclass in Provider.objects.get_queryset()._get_subclasses_recurse(Provider):
            qs = qs.select_related(subclass)
        return qs.get(pk=provider_pk)

    def test_get_deepest_child_grandparent_to_parent(self):
        """Provider -> OAuth2Provider (non-leaf subclass)."""
        oauth2 = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        provider = Provider.objects.select_related("oauth2provider").get(pk=oauth2.pk)

        resolved = get_deepest_child(provider)

        self.assertIsInstance(resolved, OAuth2Provider)
        self.assertEqual(resolved.pk, oauth2.pk)

    def test_get_deepest_child_grandparent_to_leaf(self):
        """Provider -> LDAPProvider (single-level leaf subclass)."""
        ldap = LDAPProvider.objects.create(name=generate_id())
        provider = Provider.objects.select_related("ldapprovider").get(pk=ldap.pk)

        resolved = get_deepest_child(provider)

        self.assertIsInstance(resolved, LDAPProvider)
        self.assertEqual(resolved.pk, ldap.pk)

    def test_get_deepest_child_grandparent_to_grandchild(self):
        """Provider -> OAuth2Provider -> ProxyProvider."""
        proxy = ProxyProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            external_host=f"https://{generate_id()}.goauthentik.io",
        )
        provider = Provider.objects.select_related("oauth2provider__proxyprovider").get(pk=proxy.pk)

        resolved = get_deepest_child(provider)

        self.assertIsInstance(resolved, ProxyProvider)
        self.assertEqual(resolved.pk, proxy.pk)

    def test_get_deepest_child_parent_to_child(self):
        """OAuth2Provider -> ProxyProvider (start from non-root)."""
        proxy = ProxyProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            external_host=f"https://{generate_id()}.goauthentik.io",
        )
        parent = OAuth2Provider.objects.select_related("proxyprovider").get(pk=proxy.pk)

        resolved = get_deepest_child(parent)

        self.assertIsInstance(resolved, ProxyProvider)
        self.assertEqual(resolved.pk, proxy.pk)

    def test_get_deepest_child_no_queries_with_preloaded_relations(self):
        """When all subclass relations are preloaded, no additional queries are needed."""
        proxy = ProxyProvider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            external_host=f"https://{generate_id()}.goauthentik.io",
        )
        provider = self._get_provider_with_all_subclasses(proxy.pk)

        with self.assertNumQueries(0):
            resolved = get_deepest_child(provider)

        self.assertIsInstance(resolved, ProxyProvider)
