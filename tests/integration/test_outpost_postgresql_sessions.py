"""Tests for PostgreSQL session persistence in outposts"""

from base64 import b64encode
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase
from kubernetes.client import CoreV1Api, V1Secret, V1ObjectMeta, V1SecretList

from authentik.core.tests.utils import create_test_flow
from authentik.outposts.controllers.k8s.deployment import (
    DeploymentReconciler,
    POSTGRESQL_ENV_VARS,
)
from authentik.outposts.controllers.k8s.triggers import NeedsUpdate
from authentik.outposts.models import KubernetesServiceConnection, Outpost, OutpostType
from authentik.outposts.tasks import outpost_connection_discovery
from authentik.providers.proxy.controllers.kubernetes import ProxyKubernetesController
from authentik.providers.proxy.models import ProxyProvider


class OutpostPostgreSQLSessionTests(TestCase):
    """Test PostgreSQL session persistence configuration"""

    def setUp(self):
        super().setUp()
        outpost_connection_discovery.send()
        self.provider: ProxyProvider = ProxyProvider.objects.create(
            name="test",
            internal_host="http://localhost",
            external_host="http://localhost",
            authorization_flow=create_test_flow(),
        )
        self.service_connection = KubernetesServiceConnection.objects.first()
        self.outpost: Outpost = Outpost.objects.create(
            name="test",
            type=OutpostType.PROXY,
            service_connection=self.service_connection,
        )
        self.outpost.providers.add(self.provider)
        self.outpost.save()

    def test_session_backend_postgres_triggers_update(self):
        """Test that changing session_backend to postgres triggers deployment update"""
        controller = ProxyKubernetesController(self.outpost, self.service_connection)
        deployment_reconciler = DeploymentReconciler(controller)
        
        current = deployment_reconciler.get_reference_object()
        
        # Change session backend
        config = self.outpost.config
        config.session_backend = "postgres"
        config.kubernetes_postgresql_secret_name = "test-pg-secret"
        self.outpost.config = config
        self.outpost.save()
        
        reference = deployment_reconciler.get_reference_object()
        
        # Should trigger update due to envFrom change
        with self.assertRaises(NeedsUpdate):
            deployment_reconciler.reconcile(current, reference)

    def test_envform_added_when_postgres_enabled(self):
        """Test that envFrom is added when session_backend is postgres"""
        config = self.outpost.config
        config.session_backend = "postgres"
        config.kubernetes_postgresql_secret_name = "test-pg-secret"
        self.outpost.config = config
        self.outpost.save()
        
        controller = ProxyKubernetesController(self.outpost, self.service_connection)
        deployment_reconciler = DeploymentReconciler(controller)
        
        deployment = deployment_reconciler.get_reference_object()
        container = deployment.spec.template.spec.containers[0]
        
        self.assertIsNotNone(container.env_from)
        self.assertEqual(len(container.env_from), 1)
        self.assertEqual(container.env_from[0].secret_ref.name, "test-pg-secret")

    def test_envform_not_added_when_postgres_disabled(self):
        """Test that envFrom is not added when session_backend is not postgres"""
        controller = ProxyKubernetesController(self.outpost, self.service_connection)
        deployment_reconciler = DeploymentReconciler(controller)
        
        deployment = deployment_reconciler.get_reference_object()
        container = deployment.spec.template.spec.containers[0]
        
        # envFrom should be empty or None
        self.assertTrue(not container.env_from or len(container.env_from) == 0)

    @patch.object(CoreV1Api, "read_namespaced_secret")
    def test_file_reference_detection_with_volume_mount(self, mock_read_secret):
        """Test that file:// references are detected and volume is mounted"""
        # Mock secret with file:// references
        secret_data = {
            POSTGRESQL_ENV_VARS[0]: b64encode(b"file:///db-creds/username").decode(),
            POSTGRESQL_ENV_VARS[1]: b64encode(b"file:///db-creds/password").decode(),
            POSTGRESQL_ENV_VARS[2]: b64encode(b"file:///db-creds/database").decode(),
        }
        mock_secret = V1Secret(
            metadata=V1ObjectMeta(name="test-pg-secret"),
            data=secret_data,
        )
        mock_read_secret.return_value = mock_secret
        
        # Mock list secrets for auto-detection
        with patch.object(CoreV1Api, "list_namespaced_secret") as mock_list:
            creds_secret = V1Secret(
                metadata=V1ObjectMeta(name="test-db-credentials"),
                data={
                    "username": b64encode(b"testuser").decode(),
                    "password": b64encode(b"testpass").decode(),
                    "database": b64encode(b"testdb").decode(),
                },
            )
            mock_list.return_value = V1SecretList(items=[creds_secret])
            
            config = self.outpost.config
            config.session_backend = "postgres"
            config.kubernetes_postgresql_secret_name = "test-pg-secret"
            self.outpost.config = config
            self.outpost.save()
            
            controller = ProxyKubernetesController(self.outpost, self.service_connection)
            deployment_reconciler = DeploymentReconciler(controller)
            
            deployment = deployment_reconciler.get_reference_object()
            
            # Check volume is added
            self.assertIsNotNone(deployment.spec.template.spec.volumes)
            self.assertEqual(len(deployment.spec.template.spec.volumes), 1)
            volume = deployment.spec.template.spec.volumes[0]
            self.assertEqual(volume.name, "db-creds")
            self.assertEqual(volume.secret.secret_name, "test-db-credentials")
            
            # Check volume mount is added
            container = deployment.spec.template.spec.containers[0]
            self.assertIsNotNone(container.volume_mounts)
            self.assertEqual(len(container.volume_mounts), 1)
            mount = container.volume_mounts[0]
            self.assertEqual(mount.name, "db-creds")
            self.assertEqual(mount.mount_path, "/db-creds")
            self.assertTrue(mount.read_only)

    @patch.object(CoreV1Api, "read_namespaced_secret")
    def test_volume_not_added_without_file_references(self, mock_read_secret):
        """Test that volume is not added when secret has no file:// references"""
        # Mock secret with direct values (no file://)
        secret_data = {
            POSTGRESQL_ENV_VARS[0]: b64encode(b"testuser").decode(),
            POSTGRESQL_ENV_VARS[1]: b64encode(b"testpass").decode(),
            POSTGRESQL_ENV_VARS[2]: b64encode(b"testdb").decode(),
        }
        mock_secret = V1Secret(
            metadata=V1ObjectMeta(name="test-pg-secret"),
            data=secret_data,
        )
        mock_read_secret.return_value = mock_secret
        
        config = self.outpost.config
        config.session_backend = "postgres"
        config.kubernetes_postgresql_secret_name = "test-pg-secret"
        self.outpost.config = config
        self.outpost.save()
        
        controller = ProxyKubernetesController(self.outpost, self.service_connection)
        deployment_reconciler = DeploymentReconciler(controller)
        
        deployment = deployment_reconciler.get_reference_object()
        
        # Volume should not be added
        self.assertTrue(
            not deployment.spec.template.spec.volumes
            or len(deployment.spec.template.spec.volumes) == 0
        )

    @patch.object(CoreV1Api, "read_namespaced_secret")
    @patch.object(CoreV1Api, "list_namespaced_secret")
    def test_explicit_credentials_secret_overrides_autodetect(
        self, mock_list_secret, mock_read_secret
    ):
        """Test that explicit credentials secret name takes precedence over auto-detection"""
        # Mock secret with file:// references
        secret_data = {
            POSTGRESQL_ENV_VARS[0]: b64encode(b"file:///creds/user").decode(),
        }
        mock_secret = V1Secret(
            metadata=V1ObjectMeta(name="pg-env-secret"),
            data=secret_data,
        )
        mock_read_secret.return_value = mock_secret
        
        # Mock two potential credential secrets
        auto_detected = V1Secret(
            metadata=V1ObjectMeta(name="auto-detected-creds"),
            data={
                "username": b64encode(b"user").decode(),
                "password": b64encode(b"pass").decode(),
                "database": b64encode(b"db").decode(),
            },
        )
        mock_list_secret.return_value = V1SecretList(items=[auto_detected])
        
        config = self.outpost.config
        config.session_backend = "postgres"
        config.kubernetes_postgresql_secret_name = "pg-env-secret"
        config.kubernetes_postgresql_credentials_secret_name = "explicit-creds"
        self.outpost.config = config
        self.outpost.save()
        
        controller = ProxyKubernetesController(self.outpost, self.service_connection)
        deployment_reconciler = DeploymentReconciler(controller)
        
        deployment = deployment_reconciler.get_reference_object()
        
        # Should use explicit secret name, not auto-detected
        if deployment.spec.template.spec.volumes:
            volume = deployment.spec.template.spec.volumes[0]
            self.assertEqual(volume.secret.secret_name, "explicit-creds")

    def test_volume_triggers_update_when_added(self):
        """Test that adding volume/volumeMount triggers deployment update"""
        controller = ProxyKubernetesController(self.outpost, self.service_connection)
        deployment_reconciler = DeploymentReconciler(controller)
        
        current = deployment_reconciler.get_reference_object()
        
        # Enable postgres with file:// references
        with patch.object(CoreV1Api, "read_namespaced_secret") as mock_read:
            secret_data = {
                POSTGRESQL_ENV_VARS[0]: b64encode(b"file:///creds/user").decode(),
            }
            mock_secret = V1Secret(
                metadata=V1ObjectMeta(name="pg-secret"),
                data=secret_data,
            )
            mock_read.return_value = mock_secret
            
            with patch.object(CoreV1Api, "list_namespaced_secret") as mock_list:
                creds_secret = V1Secret(
                    metadata=V1ObjectMeta(name="creds"),
                    data={
                        "username": b64encode(b"u").decode(),
                        "password": b64encode(b"p").decode(),
                        "database": b64encode(b"d").decode(),
                    },
                )
                mock_list.return_value = V1SecretList(items=[creds_secret])
                
                config = self.outpost.config
                config.session_backend = "postgres"
                config.kubernetes_postgresql_secret_name = "pg-secret"
                self.outpost.config = config
                self.outpost.save()
                
                reference = deployment_reconciler.get_reference_object()
                
                # Should trigger update due to volume/volumeMount changes
                with self.assertRaises(NeedsUpdate):
                    deployment_reconciler.reconcile(current, reference)
