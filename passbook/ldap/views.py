# """Supervisr Mod LDAP Views"""


# from django.contrib import messages
# from django.contrib.auth.decorators import login_required, user_passes_test
# from django.http import HttpRequest, HttpResponse
# from django.shortcuts import redirect, render
# from django.urls import reverse
# from django.utils.translation import ugettext as _

# from supervisr.mod.auth.ldap.forms import (AuthenticationBackendSettings,
#                                            ConnectionSettings,
#                                            CreateUsersSettings,
#                                            GeneralSettingsForm)


# @login_required
# @user_passes_test(lambda u: u.is_superuser)
# def admin_settings(request: HttpRequest) -> HttpResponse:
#     """Default view for modules without admin view"""
#     form_classes = {
#         'general': GeneralSettingsForm,
#         'connection': ConnectionSettings,
#         'authentication': AuthenticationBackendSettings,
#         'create_users': CreateUsersSettings,
#     }
#     render_data = {}
#     for form_key, form_class in form_classes.items():
#         render_data[form_key] = form_class(request.POST if request.method == 'POST' else None)
#     if request.method == 'POST':
#         update_count = 0
#         for form_key, form_class in form_classes.items():
#             form = form_class(request.POST)
#             if form.is_valid():
#                 update_count += form.save()
#         messages.success(request, _('Successfully updated %d settings.' % update_count))
#         return redirect(reverse('supervisr_mod_auth_ldap:admin_settings'))
#     return render(request, 'ldap/settings.html', render_data)
