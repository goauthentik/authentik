from django.db.models import Model, OneToOneField, OneToOneRel


def get_deepest_child(parent: Model) -> Model:
    """
    In multiple table inheritance, given any ancestor object, get the deepest child object.
    See https://docs.djangoproject.com/en/dev/topics/db/models/#multi-table-inheritance

    This function does not query the database if `select_related` has been performed on all
    subclasses of `parent`'s model.
    """

    # Almost verbatim copy from django-model-utils, see
    # https://github.com/jazzband/django-model-utils/blob/5.0.0/model_utils/managers.py#L132
    one_to_one_rels = [
        field for field in parent._meta.get_fields() if isinstance(field, OneToOneRel)
    ]

    submodel_fields = [
        rel
        for rel in one_to_one_rels
        if isinstance(rel.field, OneToOneField)
        and issubclass(rel.field.model, parent._meta.model)
        and parent._meta.model is not rel.field.model
        and rel.parent_link
    ]

    submodel_accessors = [submodel_field.get_accessor_name() for submodel_field in submodel_fields]
    # End Copy

    child = None
    for submodel in submodel_accessors:
        try:
            child = getattr(parent, submodel)
            break
        except AttributeError:
            continue

    if not child:
        return parent
    return get_deepest_child(child)
