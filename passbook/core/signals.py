"""passbook core signals"""

from django.core.signals import Signal

# from django.db.models.signals import post_save, pre_delete
# from django.dispatch import receiver
# from passbook.core.models import Invite, User

user_signed_up = Signal(providing_args=['request', 'user'])
# TODO: Send this signal in admin interface
invite_created = Signal(providing_args=['request', 'invite'])
invite_used = Signal(providing_args=['request', 'invite', 'user'])
