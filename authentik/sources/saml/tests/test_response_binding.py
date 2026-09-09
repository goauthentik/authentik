"""SAML Source response binding tests"""

from base64 import b64encode

from django.core.exceptions import SuspiciousOperation
from django.test import TestCase
from freezegun import freeze_time

from authentik.core.tests.utils import RequestFactory, create_test_flow
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture
from authentik.sources.saml.exceptions import (
    MismatchedBinding,
    MismatchedRequestID,
    SAMLException,
)
from authentik.sources.saml.models import SAMLSource
from authentik.sources.saml.processors.request import SESSION_KEY_REQUEST_ID
from authentik.sources.saml.processors.response import ResponseProcessor

# This source.
SOURCE_SLUG = "another-idp"
ENTITY_ID = "https://authentik.company/source/saml/another-idp/metadata/"
ACS_URL = "http://testserver/source/saml/another-idp/acs/"
# The ID of the AuthNRequest that this source sent to the IdP.
REQUEST_ID = "_our_request_id"
# The end of the validity of the assertion. The tests run at 14:15:00.
VALID_UNTIL = "2022-10-14T14:16:49Z"
# A second service provider that uses the same IdP as this source.
OTHER_ACS_URL = "https://other-app.example/acs"
OTHER_REQUEST_ID = "_other_app_request_id"


@freeze_time("2022-10-14T14:15:00Z")
class TestResponseBinding(TestCase):
    """Test that a Response must be addressed to this source"""

    def setUp(self):
        self.factory = RequestFactory()
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=SOURCE_SLUG,
            issuer=ENTITY_ID,
            pre_authentication_flow=create_test_flow(),
        )

    def test_addressed_to_this_source(self):
        """A response that names this source is accepted"""
        response = load_fixture(
            "fixtures/response_binding.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        ResponseProcessor(self.source, request).parse()

    def test_minimal_response(self):
        """A response that carries none of the optional values is accepted"""
        response = load_fixture(
            "fixtures/response_binding_minimal.xml",
            response_in_response_to=REQUEST_ID,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        ResponseProcessor(self.source, request).parse()

    def test_no_confirmation(self):
        """An assertion that carries no confirmation of the subject is refused"""
        response = load_fixture(
            "fixtures/response_binding_no_confirmation.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedBinding):
            ResponseProcessor(self.source, request).parse()

    def test_confirmation_without_data(self):
        """A confirmation of the subject that carries no data is refused"""
        response = load_fixture(
            "fixtures/response_binding_confirmation_without_data.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedBinding):
            ResponseProcessor(self.source, request).parse()

    def test_recipient_other_sp(self):
        """The Recipient must name the ACS URL of this source"""
        response = load_fixture(
            "fixtures/response_binding.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=OTHER_ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedBinding):
            ResponseProcessor(self.source, request).parse()

    def test_recipient_other_case(self):
        """Only the case of the Recipient can differ from the ACS URL"""
        response = load_fixture(
            "fixtures/response_binding.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=ACS_URL.upper(),
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        ResponseProcessor(self.source, request).parse()

    def test_other_confirmation_method_first(self):
        """An assertion can carry more than one confirmation of the subject. Satisfying the
        one that names this source is enough."""
        response = load_fixture(
            "fixtures/response_binding_two_confirmations.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            other_recipient=OTHER_ACS_URL,
            other_in_response_to=OTHER_REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        ResponseProcessor(self.source, request).parse()

    def test_confirmation_other_method(self):
        """A confirmation that names another confirmation method is not read, even when it
        names this source, so an assertion that carries only that one is refused"""
        response = load_fixture(
            "fixtures/response_binding_other_method.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedBinding):
            ResponseProcessor(self.source, request).parse()

    def test_other_method_confirmation_constrains_nothing(self):
        """A confirmation that names another confirmation method does not confirm the
        subject for this source, not even when it constrains nothing"""
        response = load_fixture(
            "fixtures/response_binding_other_method_and_bearer.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=OTHER_ACS_URL,
            assertion_in_response_to=OTHER_REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedBinding):
            ResponseProcessor(self.source, request).parse()

    def test_confirmation_without_method(self):
        """A confirmation of the subject that names no method is read"""
        response = load_fixture(
            "fixtures/response_binding_no_method.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        ResponseProcessor(self.source, request).parse()

    def test_no_confirmation_names_this_source(self):
        """One confirmation of the subject must name this source"""
        response = load_fixture(
            "fixtures/response_binding_two_confirmations.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            other_recipient=OTHER_ACS_URL,
            other_in_response_to=OTHER_REQUEST_ID,
            recipient=OTHER_ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedBinding):
            ResponseProcessor(self.source, request).parse()

    def test_recipient_other_scheme(self):
        """A Recipient that names another scheme does not match. A deployment whose reverse
        proxy does not send X-Forwarded-Proto builds the ACS URL with the wrong scheme."""
        response = load_fixture(
            "fixtures/response_binding.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient="https://testserver/source/saml/another-idp/acs/",
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedBinding):
            ResponseProcessor(self.source, request).parse()

    def test_recipient_other_port(self):
        """A Recipient that names another port does not match"""
        response = load_fixture(
            "fixtures/response_binding.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient="http://testserver:80/source/saml/another-idp/acs/",
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedBinding):
            ResponseProcessor(self.source, request).parse()

    def test_destination_other_sp(self):
        """The Destination must name the ACS URL of this source"""
        response = load_fixture(
            "fixtures/response_binding.xml",
            destination=OTHER_ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedBinding):
            ResponseProcessor(self.source, request).parse()

    def test_in_response_to_of_assertion(self):
        """The InResponseTo of the assertion must be the ID of our own request"""
        response = load_fixture(
            "fixtures/response_binding.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=OTHER_REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedRequestID):
            ResponseProcessor(self.source, request).parse()

    def test_in_response_to_of_response(self):
        """The InResponseTo of the response must be the ID of our own request"""
        response = load_fixture(
            "fixtures/response_binding.xml",
            destination=ACS_URL,
            response_in_response_to=OTHER_REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(MismatchedRequestID):
            ResponseProcessor(self.source, request).parse()

    def test_subject_confirmation_expired(self):
        """The NotOnOrAfter of the SubjectConfirmationData is checked"""
        response = load_fixture(
            "fixtures/response_binding.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after="2022-10-14T14:14:00Z",
        )
        request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        request.session.save()

        with self.assertRaises(SAMLException):
            ResponseProcessor(self.source, request).parse()

    def test_assertion_used_two_times(self):
        """One assertion is accepted one time only"""
        response = load_fixture(
            "fixtures/response_binding.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        first_request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        first_request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        first_request.session.save()
        second_request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(response.encode()).decode()}
        )
        second_request.session[SESSION_KEY_REQUEST_ID] = REQUEST_ID
        second_request.session.save()

        ResponseProcessor(self.source, first_request).parse()
        with self.assertRaises(SuspiciousOperation):
            ResponseProcessor(self.source, second_request).parse()

    def test_assertion_used_two_times_idp_initiated(self):
        """A new ID on the response does not make a used assertion valid again"""
        self.source.allow_idp_initiated = True
        self.source.save()
        first_response = load_fixture(
            "fixtures/response_binding.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        second_response = load_fixture(
            "fixtures/response_binding_other_response_id.xml",
            destination=ACS_URL,
            response_in_response_to=REQUEST_ID,
            recipient=ACS_URL,
            assertion_in_response_to=REQUEST_ID,
            subject_not_on_or_after=VALID_UNTIL,
        )
        first_request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(first_response.encode()).decode()}
        )
        second_request = self.factory.post(
            "/", data={"SAMLResponse": b64encode(second_response.encode()).decode()}
        )

        ResponseProcessor(self.source, first_request).parse()
        with self.assertRaises(SuspiciousOperation):
            ResponseProcessor(self.source, second_request).parse()
