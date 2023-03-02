"""SCIM Provider tasks"""
from django.core.paginator import Paginator
from django.utils.text import slugify
from structlog.stdlib import get_logger

from authentik.core.models import Group, User
from authentik.events.monitored_tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.providers.scim.clients import PAGE_SIZE
from authentik.providers.scim.clients.base import SCIMClient
from authentik.providers.scim.clients.exceptions import SCIMRequestError
from authentik.providers.scim.clients.group import SCIMGroupClient
from authentik.providers.scim.clients.user import SCIMUserClient
from authentik.providers.scim.models import SCIMProvider
from authentik.root.celery import CELERY_APP

LOGGER = get_logger(__name__)


@CELERY_APP.task(bind=True, base=MonitoredTask)
def scim_sync_full(self: MonitoredTask, provider_pk: int) -> None:
    """Run SCIM full sync for provider"""
    provider: SCIMProvider = SCIMProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        return
    self.set_uid(slugify(provider.name))
    # TODO: Filtering
    LOGGER.debug("Starting SCIM sync")
    users_paginator = Paginator(User.objects.all().order_by("pk"), PAGE_SIZE)
    groups_paginator = Paginator(Group.objects.all().order_by("pk"), PAGE_SIZE)
    for page in users_paginator.page_range:
        scim_sync_users.delay(page, provider_pk)
    for page in groups_paginator.page_range:
        scim_sync_group.delay(page, provider_pk)
    self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL))


@CELERY_APP.task()
def scim_sync_users(page: int, provider_pk):
    """Sync single or multiple users to SCIM"""
    provider: SCIMProvider = SCIMProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        return
    client = SCIMClient(provider)
    user_client = SCIMUserClient(client)
    paginator = Paginator(User.objects.all().order_by("pk"), PAGE_SIZE)
    LOGGER.debug("starting user sync for page", page=page)
    for user in paginator.page(page).object_list:
        try:
            user_client.write(user)
        except SCIMRequestError as exc:
            LOGGER.warning("failed to sync user", exc=exc, user=user)


@CELERY_APP.task()
def scim_sync_group(page: int, provider_pk):
    """Sync single or multiple groups to SCIM"""
    provider: SCIMProvider = SCIMProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        return
    client = SCIMClient(provider)
    group_client = SCIMGroupClient(client)
    paginator = Paginator(Group.objects.all().order_by("pk"), PAGE_SIZE)
    LOGGER.debug("starting group sync for page", page=page)
    for group in paginator.page(page).object_list:
        try:
            group_client.write(group)
        except SCIMRequestError as exc:
            LOGGER.warning("failed to sync group", exc=exc, group=group)
