"""passbook core signals"""

from django.core.signals import Signal

# from django.db.models.signals import post_save, pre_delete
# from django.dispatch import receiver
# from passbook.core.models import Invitation, User

user_signed_up = Signal(providing_args=['request', 'user'])
invitation_created = Signal(providing_args=['request', 'invitation'])
invitation_used = Signal(providing_args=['request', 'invitation', 'user'])
password_changed = Signal(providing_args=['user', 'password'])
