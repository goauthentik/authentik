"""passbook nexus_upload management command"""
from base64 import b64decode

import requests
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Upload debian package to nexus repository"""

    url = None
    user = None
    password = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--repo',
            action='store',
            help='Repository to upload to',
            required=True)
        parser.add_argument(
            '--url',
            action='store',
            help='Nexus root URL',
            required=True)
        parser.add_argument(
            '--auth',
            action='store',
            help='base64-encoded string of username:password',
            required=True)
        parser.add_argument(
            '--method',
            action='store',
            nargs='?',
            const='post',
            choices=['post', 'put'],
            help=('Method used for uploading files to nexus. '
                  'Apt repositories use post, Helm uses put.'),
            required=True)
        # Positional arguments
        parser.add_argument('file', nargs='+', type=str)

    def handle(self, *args, **options):
        """Upload debian package to nexus repository"""
        auth = tuple(b64decode(options.get('auth')).decode('utf-8').split(':', 1))
        responses = {}
        url = 'https://%(url)s/repository/%(repo)s/' % options
        method = options.get('method')
        exit_code = 0
        for file in options.get('file'):
            if method == 'post':
                responses[file] = requests.post(url, data=open(file, mode='rb'), auth=auth)
            else:
                responses[file] = requests.put(url+file, data=open(file, mode='rb'), auth=auth)
        self.stdout.write('Upload results:\n')
        sep = '-' * 60
        self.stdout.write('%s\n' % sep)
        for path, response in responses.items():
            self.stdout.write('%-55s: %d\n' % (path, response.status_code))
            if response.status_code >= 400:
                exit_code = 1
        self.stdout.write('%s\n' % sep)
        exit(exit_code)
