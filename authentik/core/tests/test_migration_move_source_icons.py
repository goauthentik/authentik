"""Test moving stored built-in source icons to their themed folders"""

from importlib import import_module

from django.apps import apps
from django.db import connection
from django.test import TestCase

from authentik.core.models import Application
from authentik.flows.models import Flow, FlowDesignation
from authentik.lib.generators import generate_id
from authentik.sources.oauth.models import OAuthSource

move_source_icons = import_module(
    "authentik.core.migrations.0067_move_source_icons"
).move_source_icons


class TestMoveSourceIcons(TestCase):
    """Test moving stored built-in source icons to their themed folders"""

    def test_move(self):
        """Test built-in icons are moved, other values are kept"""
        github = OAuthSource.objects.create(
            name=generate_id(), slug=generate_id(), icon="/static/authentik/sources/github.svg"
        )
        custom = OAuthSource.objects.create(
            name=generate_id(), slug=generate_id(), icon="sources/github.svg"
        )
        app = Application.objects.create(
            name=generate_id(), slug=generate_id(), meta_icon="/static/authentik/sources/ldap.png"
        )
        flow = Flow.objects.create(
            name=generate_id(),
            slug=generate_id(),
            designation=FlowDesignation.AUTHENTICATION,
            background="/static/authentik/sources/kerberos.png",
        )

        with connection.schema_editor() as schema_editor:
            move_source_icons(apps, schema_editor)

        github.refresh_from_db()
        custom.refresh_from_db()
        app.refresh_from_db()
        flow.refresh_from_db()
        self.assertEqual(github.icon, "/static/authentik/sources/github/%(theme)s.svg")
        self.assertEqual(custom.icon, "sources/github.svg")
        self.assertEqual(app.meta_icon, "/static/authentik/sources/ldap/%(theme)s.svg")
        self.assertEqual(flow.background, "/static/authentik/sources/kerberos/%(theme)s.png")
