"""Test Utils"""
from django.utils.text import slugify

from authentik.flows.models import Flow, FlowDesignation
from authentik.lib.generators import generate_id


def create_test_flow(designation: FlowDesignation = FlowDesignation.STAGE_CONFIGURATION) -> Flow:
    """Generate a flow that can be used for testing"""
    uid = generate_id(10)
    return Flow.objects.create(
        name=uid,
        title=uid,
        slug=slugify(uid),
        designation=designation,
    )
