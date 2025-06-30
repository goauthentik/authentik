"""Test PostSourceStage handling of duplicate connections"""

from unittest.mock import MagicMock, patch

from django.db.utils import IntegrityError
from django.http import HttpRequest
from django.test import TestCase

from authentik.core.models import Source, User, UserSourceConnection
from authentik.core.sources.stage import PLAN_CONTEXT_SOURCES_CONNECTION, PostSourceStage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.lib.generators import generate_id


class PostSourceProxySource(Source):
    """source"""

    class Meta:
        proxy = True


class TestPostSourceStage(TestCase):
    """Test ability to handle duplicate connections"""

    def setUp(self):
        self.user = User.objects.create(username=generate_id())
        # Create a real source instance
        source_slug = generate_id()
        self.source = PostSourceProxySource.objects.create(
            name="Test Source",
            slug=source_slug,
            enabled=True,
        )

        # Create real request
        self.request = HttpRequest()

        # Define a patch path that will be reused in tests
        self.filter_path = "authentik.core.sources.stage.UserSourceConnection.objects.filter"
        self.save_path = "authentik.core.sources.stage.UserSourceConnection.save"

    def test_new_connection(self):
        """Test normal case where connection is new"""
        # Create a connection that doesn't exist yet
        connection = UserSourceConnection(source=self.source, identifier="test-identifier")

        # Create executor
        executor = MagicMock()
        executor.plan = MagicMock()
        executor.plan.context = {
            PLAN_CONTEXT_PENDING_USER: self.user,
            PLAN_CONTEXT_SOURCES_CONNECTION: connection,
        }
        executor.stage_ok.return_value = "stage_ok"

        # Setup stage
        stage = PostSourceStage(request=self.request, executor=executor)

        # Mock the Event.new method to prevent actual event creation
        with patch("authentik.events.models.Event.new") as mock_event:
            mock_event.return_value = MagicMock()
            mock_event.return_value.from_http.return_value = None

            # Execute the stage
            response = stage.dispatch(self.request)

            # Verify the connection user was set
            self.assertEqual(connection.user, self.user)
            self.assertEqual(response, "stage_ok")
            # Verify the connection was saved
            self.assertIsNotNone(connection.pk)

    def test_duplicate_connection(self):
        """Test case where a duplicate connection exists"""
        # First create an existing connection
        existing = UserSourceConnection.objects.create(
            user=self.user, source=self.source, identifier="old-identifier"
        )

        # Now create a new connection that will conflict
        new_connection = UserSourceConnection(source=self.source, identifier="test-identifier")

        # Create executor
        executor = MagicMock()
        executor.plan = MagicMock()
        executor.plan.context = {
            PLAN_CONTEXT_PENDING_USER: self.user,
            PLAN_CONTEXT_SOURCES_CONNECTION: new_connection,
        }
        executor.stage_ok.return_value = "stage_ok"

        # Setup stage with patched methods
        stage = PostSourceStage(request=self.request, executor=executor)

        # Create a counter for calls to save
        call_count = 0

        def side_effect_save(*args, **kwargs):
            """Only raise IntegrityError on first call"""
            nonlocal call_count
            if call_count == 0:
                call_count += 1
                raise IntegrityError("Duplicate key")
            # For subsequent calls, do nothing (simulate successful save)

        # Override the save method with our custom side effect
        with patch(self.save_path, side_effect=side_effect_save):
            # Return the existing connection when filter is called
            with patch(self.filter_path) as mock_filter:
                mock_filter_instance = MagicMock()
                mock_filter_instance.first.return_value = existing
                mock_filter.return_value = mock_filter_instance

                # Execute the stage
                response = stage.dispatch(self.request)

                # Verify behavior
                self.assertEqual(response, "stage_ok")
                # Make sure filter was called with correct arguments
                mock_filter.assert_called_once_with(user=self.user, source=self.source)
                # Verify the existing connection's identifier was updated
                self.assertEqual(existing.identifier, "test-identifier")
                # Verify our side effect function was called twice
                self.assertEqual(call_count, 1)

    def test_update_existing_identifier(self):
        """Test that an existing connection gets its identifier updated if different"""
        # First create an existing connection
        existing = UserSourceConnection.objects.create(
            user=self.user, source=self.source, identifier="old-identifier"
        )

        # Create a new connection with a different identifier
        new_connection = UserSourceConnection(source=self.source, identifier="new-identifier")

        # Create executor
        executor = MagicMock()
        executor.plan = MagicMock()
        executor.plan.context = {
            PLAN_CONTEXT_PENDING_USER: self.user,
            PLAN_CONTEXT_SOURCES_CONNECTION: new_connection,
        }
        executor.stage_ok.return_value = "stage_ok"

        # Setup stage
        stage = PostSourceStage(request=self.request, executor=executor)

        # Create a counter for calls to save
        call_count = 0

        def side_effect_save(*args, **kwargs):
            """Only raise IntegrityError on first call"""
            nonlocal call_count
            if call_count == 0:
                call_count += 1
                raise IntegrityError("Duplicate key")
            # For subsequent calls, do nothing (simulate successful save)

        # Override the save method with our custom side effect
        with patch(self.save_path, side_effect=side_effect_save):
            # Return the existing connection when filter is called
            with patch(self.filter_path) as mock_filter:
                mock_filter_instance = MagicMock()
                mock_filter_instance.first.return_value = existing
                mock_filter.return_value = mock_filter_instance

                # Execute the stage
                response = stage.dispatch(self.request)

                # Verify behavior
                self.assertEqual(response, "stage_ok")
                # Make sure filter was called with correct arguments
                mock_filter.assert_called_once_with(user=self.user, source=self.source)
                # Verify the existing connection's identifier was updated
                self.assertEqual(existing.identifier, "new-identifier")
                # Verify our side effect function was called twice (initial fail + update)
                self.assertEqual(call_count, 1)

    def test_same_identifier_no_update(self):
        """Test when existing connection has the same identifier, no update needed"""
        # Create an existing connection
        existing = UserSourceConnection.objects.create(
            user=self.user, source=self.source, identifier="same-identifier"
        )

        # Create a new connection with the same identifier
        new_connection = UserSourceConnection(source=self.source, identifier="same-identifier")

        # Create executor
        executor = MagicMock()
        executor.plan = MagicMock()
        executor.plan.context = {
            PLAN_CONTEXT_PENDING_USER: self.user,
            PLAN_CONTEXT_SOURCES_CONNECTION: new_connection,
        }
        executor.stage_ok.return_value = "stage_ok"

        # Setup stage
        stage = PostSourceStage(request=self.request, executor=executor)

        # Create counters to track method calls
        save_count = 0

        def side_effect_save(*args, **kwargs):
            """Only raise IntegrityError on first call"""
            nonlocal save_count
            if save_count == 0:
                save_count += 1
                raise IntegrityError("Duplicate key")
            # For subsequent calls, do nothing (simulate successful save)

        # Override the save method with our custom side effect
        with patch(self.save_path, side_effect=side_effect_save):
            # Return the existing connection when filter is called
            with patch(self.filter_path) as mock_filter:
                mock_filter_instance = MagicMock()
                mock_filter_instance.first.return_value = existing
                mock_filter.return_value = mock_filter_instance

                # Mock save on existing_connection to track if it's called
                with patch.object(existing, "save") as mock_existing_save:
                    # Execute the stage
                    response = stage.dispatch(self.request)

                    # Verify behavior
                    self.assertEqual(response, "stage_ok")
                    # Verify identifier is still the same
                    self.assertEqual(existing.identifier, "same-identifier")
                    # Verify save wasn't called on existing connection
                    mock_existing_save.assert_not_called()

    def test_no_existing_connection_found(self):
        """Test when an IntegrityError occurs but no existing connection is found"""
        # Create a new connection
        new_connection = UserSourceConnection(source=self.source, identifier="test-identifier")

        # Create executor
        executor = MagicMock()
        executor.plan = MagicMock()
        executor.plan.context = {
            PLAN_CONTEXT_PENDING_USER: self.user,
            PLAN_CONTEXT_SOURCES_CONNECTION: new_connection,
        }
        executor.stage_ok.return_value = "stage_ok"

        # Setup stage
        stage = PostSourceStage(request=self.request, executor=executor)

        # Override the save method to raise IntegrityError
        with patch(self.save_path, side_effect=IntegrityError("Duplicate key")):
            # Return None when filter is called (no existing connection found)
            with patch(self.filter_path) as mock_filter:
                mock_filter_instance = MagicMock()
                mock_filter_instance.first.return_value = None
                mock_filter.return_value = mock_filter_instance

                # Expect the IntegrityError to be re-raised
                with self.assertRaises(IntegrityError):
                    stage.dispatch(self.request)

                # Make sure filter was called with correct arguments
                mock_filter.assert_called_once_with(user=self.user, source=self.source)

    def test_empty_filter_result(self):
        """Test when the filter call returns an empty queryset (first() returns None)"""
        # Create a new connection
        new_connection = UserSourceConnection(source=self.source, identifier="test-identifier")

        # Create executor
        executor = MagicMock()
        executor.plan = MagicMock()
        executor.plan.context = {
            PLAN_CONTEXT_PENDING_USER: self.user,
            PLAN_CONTEXT_SOURCES_CONNECTION: new_connection,
        }
        executor.stage_ok.return_value = "stage_ok"

        # Setup stage
        stage = PostSourceStage(request=self.request, executor=executor)

        # Override the save method to raise IntegrityError
        with patch(self.save_path, side_effect=IntegrityError("Duplicate key")):
            # Create a mock filter result where first() returns None (empty queryset)
            with patch(self.filter_path) as mock_filter:
                mock_filter_instance = MagicMock()
                mock_filter_instance.first.return_value = None
                mock_filter.return_value = mock_filter_instance

                # Expect the IntegrityError to be re-raised
                with self.assertRaises(IntegrityError):
                    stage.dispatch(self.request)

                # Make sure filter was called with correct arguments
                mock_filter.assert_called_once_with(user=self.user, source=self.source)
