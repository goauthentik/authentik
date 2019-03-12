from __future__ import absolute_import, print_function

from django import forms

from sentry.auth.view import AuthView, ConfigureView
from sentry.models import AuthIdentity

from .client import PassbookClient


def _get_name_from_email(email):
    """
    Given an email return a capitalized name. Ex. john.smith@example.com would return John Smith.
    """
    name = email.rsplit('@', 1)[0]
    name = ' '.join([n_part.capitalize() for n_part in name.split('.')])
    return name


class FetchUser(AuthView):
    def __init__(self, client_id, client_secret, *args, **kwargs):
        self.client = PassbookClient(client_id, client_secret)
        super(FetchUser, self).__init__(*args, **kwargs)

    def handle(self, request, helper):
        access_token = helper.fetch_state('data')['access_token']

        user = self.client.get_user(access_token)

        # A user hasn't set their name in their Passbook profile so it isn't
        # populated in the response
        if not user.get('name'):
            user['name'] = _get_name_from_email(user['email'])

        helper.bind_state('user', user)

        return helper.next_step()


class ConfirmEmailForm(forms.Form):
    email = forms.EmailField(label='Email')


class ConfirmEmail(AuthView):
    def handle(self, request, helper):
        user = helper.fetch_state('user')

        # TODO(dcramer): this isnt ideal, but our current flow doesnt really
        # support this behavior;
        try:
            auth_identity = AuthIdentity.objects.select_related('user').get(
                auth_provider=helper.auth_provider,
                ident=user['id'],
            )
        except AuthIdentity.DoesNotExist:
            pass
        else:
            user['email'] = auth_identity.user.email

        if user.get('email'):
            return helper.next_step()

        form = ConfirmEmailForm(request.POST or None)
        if form.is_valid():
            user['email'] = form.cleaned_data['email']
            helper.bind_state('user', user)
            return helper.next_step()

        return self.respond('sentry_auth_passbook/enter-email.html', {
            'form': form,
        })

class PassbookConfigureView(ConfigureView):
    def dispatch(self, request, organization, auth_provider):
        return self.render('sentry_auth_passbook/configure.html')
