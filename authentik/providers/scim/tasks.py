"""SCIM Provider tasks"""
from django.core.paginator import Paginator
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.user import SCIMUserClient
from authentik.providers.scim.models import SCIMProvider
from authentik.root.celery import CELERY_APP

LOGGER = get_logger(__name__)
PAGE_SIZE = 100


@CELERY_APP.task(bind=True)
def scim_sync_full(self, provider_pk: int) -> None:
    """Run full sync for provider"""
    provider: SCIMProvider = SCIMProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        return
    # TODO: Filtering
    users_paginator = Paginator(User.objects.all(), PAGE_SIZE)
    for page in users_paginator.page_range:
        scim_sync_users.delay(page, base_url=provider.url, token=provider.token)


@CELERY_APP.task()
def scim_sync_users(page: int, provider_pk):
    """Sync single or multiple users to SCIM"""
    provider: SCIMProvider = SCIMProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        return
    client = SCIMClient(provider)
    user_client = SCIMUserClient(client)
    paginator = Paginator(User.objects.all(), PAGE_SIZE)
    LOGGER.debug("starting sync for page", page=page)
    for user in paginator.page(page).object_list:
        user_client.write_user(user)


# @CELERY_APP.task()
# def scim_sync_group(page: int, **kwargs):
#     """Sync single or multiple groups to SCIM"""
#     client = SCIMClient(**kwargs)
#     paginator = Paginator(Group.objects.all(), PAGE_SIZE)
#     LOGGER.debug("starting sync for page", page=page)
#     for group in paginator.page(page).object_list:
#         client.write_group(group)
