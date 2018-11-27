"""passbook Core Reflection templatetags Templatetag"""
from logging import getLogger

from django import template

register = template.Library()
LOGGER = getLogger(__name__)


def get_key_unique(context):
    """Get a unique key for cache based on user"""
    uniq = ''
    if 'request' in context:
        user = context.get('request').user
        if user.is_authenticated:
            uniq = context.get('request').user.email
        else:
            # This should never be reached as modlist requires admin rights
            uniq = 'anon'  # pragma: no cover
    return uniq

# @register.simple_tag(takes_context=True)
# def sv_reflection_admin_modules(context):
#     """Get a list of all modules and their admin page"""
#     key = 'sv_reflection_admin_modules_%s' % get_key_unique(context)
#     if not cache.get(key):
#         view_list = []
#         for app in get_apps():
#             title = app.title_modifier(context.request)
#             url = app.admin_url_name
#             view_list.append({
#                 'url': url,
#                 'default': True if url == SupervisrAppConfig.admin_url_name else False,
#                 'name': title,
#             })
#         sorted_list = sorted(view_list, key=lambda x: x.get('name'))
#         cache.set(key, sorted_list, 1000)
#         return sorted_list
#     return cache.get(key)  # pragma: no cover


# @register.simple_tag(takes_context=True)
# def sv_reflection_user_modules(context):
#     """Get a list of modules that have custom user settings"""
#     key = 'sv_reflection_user_modules_%s' % get_key_unique(context)
#     if not cache.get(key):
#         app_list = []
#         for app in get_apps():
#             if not app.name.startswith('supervisr.mod'):
#                 continue
#             view = app.view_user_settings
#             if view is not None:
#                 app_list.append({
#                     'title': app.title_modifier(context.request),
#                     'view': '%s:%s' % (app.label, view)
#                 })
#         sorted_list = sorted(app_list, key=lambda x: x.get('title'))
#         cache.set(key, sorted_list, 1000)
#         return sorted_list
#     return cache.get(key)  # pragma: no cover


# @register.simple_tag(takes_context=True)
# def sv_reflection_navbar_modules(context):
#     """Get a list of subapps for the navbar"""
#     key = 'sv_reflection_navbar_modules_%s' % get_key_unique(context)
#     if not cache.get(key):
#         app_list = []
#         for app in get_apps():
#             LOGGER.debug("Considering %s for Navbar", app.label)
#             title = app.title_modifier(context.request)
#             if app.navbar_enabled(context.request):
#                 index = getattr(app, 'index', None)
#                 if not index:
#                     index = '%s:index' % app.label
#                 try:
#                     reverse(index)
#                     LOGGER.debug("Module %s made it with '%s'", app.name, index)
#                     app_list.append({
#                         'label': app.label,
#                         'title': title,
#                         'index': index
#                     })
#                 except NoReverseMatch:
#                     LOGGER.debug("View '%s' not reversable, ignoring %s", index, app.name)
#         sorted_list = sorted(app_list, key=lambda x: x.get('label'))
#         cache.set(key, sorted_list, 1000)
#         return sorted_list
#     return cache.get(key)  # pragma: no cover
