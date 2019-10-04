"""passbook import_users management command"""
from csv import DictReader

from django.core.management.base import BaseCommand
from django.core.validators import EmailValidator, ValidationError
from structlog import get_logger

from passbook.core.models import User

LOGGER = get_logger()

class Command(BaseCommand):
    """Import users from CSV file"""

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('file', nargs='+', type=str)

    def handle(self, *args, **options):
        """Create Users from CSV file"""
        for file in options.get('file'):
            with open(file, 'r') as _file:
                reader = DictReader(_file)
                for user in reader:
                    LOGGER.debug('User %s', user.get('username'))
                    try:
                        # only import users with valid email addresses
                        if user.get('email'):
                            validator = EmailValidator()
                            validator(user.get('email'))
                        # use combination of username and email to check for existing user
                        if User.objects.filter(
                                username=user.get('username'),
                                email=user.get('email')).exists():
                            LOGGER.debug('User %s exists already, skipping', user.get('username'))
                        # Create user
                        User.objects.create(
                            username=user.get('username'),
                            email=user.get('email'),
                            name=user.get('name'),
                            password=user.get('password'))
                        LOGGER.debug('Created User %s', user.get('username'))
                    except ValidationError as exc:
                        LOGGER.warning('User %s caused %r, skipping', user.get('username'), exc)
                        continue
