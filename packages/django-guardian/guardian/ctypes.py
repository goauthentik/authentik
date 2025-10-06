from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.utils.module_loading import import_string

from guardian.conf import settings as guardian_settings


def get_content_type(obj: Model | type[Model]) -> Any:
    get_content_type_function = import_string(guardian_settings.GET_CONTENT_TYPE)
    return get_content_type_function(obj)


def get_default_content_type(obj: Model | type[Model]) -> ContentType:
    """Get content type for a given object using Django's content type framework.

    Parameters:
        obj (Model | Type): Object for which content type is to be fetched.

    Returns:
        Content type for the given object.

    See Also:
        https://docs.djangoproject.com/en/5.1/ref/contrib/contenttypes/

    """
    return ContentType.objects.get_for_model(obj)
