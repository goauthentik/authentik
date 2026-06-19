"""
Implementation of per object permissions for Django.
"""


def get_version():
    """Return the version string (see pyproject.toml) of the package.

    The value will comply with the [python version specifier format dicted by
    PEP440](https://packaging.python.org/en/latest/specifications/version-specifiers/#version-specifiers)

    Standards for packaging metadata — including version — are defined by PEP 621,
    which specifies how to declare version in pyproject.toml.

    The earlier PEP 396 suggests (but does not mandate) having a __version__
    attribute in __init__.py for the purposes of runtime introspection, but
    it leads to confusion in our development process to define it multiple places.

    PEP 396 has now been revoked, but it is still useful to be able to inspect
    the package version at runtime. This function retains that ability using the
    recommended importlib approach.
    """
    from importlib.metadata import version

    return version("ak-guardian")
