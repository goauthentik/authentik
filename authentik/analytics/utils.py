"""authentik analytics utils"""

from hashlib import sha256
from importlib import import_module
from typing import Any

from structlog import get_logger

from authentik import get_full_version
from authentik.analytics.models import AnalyticsMixin
from authentik.lib.utils.reflection import get_apps
from authentik.root.install_id import get_install_id
from authentik.tenants.models import Tenant
from authentik.tenants.utils import get_current_tenant

LOGGER = get_logger()


def get_analytics_apps() -> dict:
    modules = {}
    for _authentik_app in get_apps():
        try:
            module = import_module(f"{_authentik_app.name}.analytics")
        except ModuleNotFoundError:
            continue
        except ImportError as exc:
            LOGGER.warning(
                "Could not import app's analytics", app_name=_authentik_app.name, exc=exc
            )
            continue
        if not hasattr(module, "get_analytics_description") or not hasattr(
            module, "get_analytics_data"
        ):
            LOGGER.debug(
                "App does not define API URLs",
                app_name=_authentik_app.name,
            )
            continue
        modules[_authentik_app.label] = module
    return modules


def get_analytics_apps_description() -> dict[str, str]:
    result = {}
    for app_label, module in get_analytics_apps().items():
        for k, v in module.get_analytics_description().items():
            result[f"{app_label}/app/{k}"] = v
    return result


def get_analytics_apps_data() -> dict[str, Any]:
    result = {}
    for app_label, module in get_analytics_apps().items():
        for k, v in module.get_analytics_data().items():
            result[f"{app_label}/app/{k}"] = v
    return result


def get_analytics_models() -> list[AnalyticsMixin]:
    def get_subclasses(cls):
        for subclass in cls.__subclasses__():
            if subclass.__subclasses__():
                yield from get_subclasses(subclass)
            elif not subclass._meta.abstract:
                yield subclass

    return list(get_subclasses(AnalyticsMixin))


def get_analytics_models_description() -> dict[str, str]:
    result = {}
    for model in get_analytics_models():
        for k, v in model.get_analytics_description().items():
            result[f"{model._meta.app_label}/models/{model._meta.object_name}/{k}"] = v
    return result


def get_analytics_models_data() -> dict[str, Any]:
    result = {}
    for model in get_analytics_models():
        for k, v in model.get_analytics_data().items():
            result[f"{model._meta.app_label}/models/{model._meta.object_name}/{k}"] = v
    return result


def get_analytics_description() -> dict[str, str]:
    return {
        **get_analytics_apps_description(),
        **get_analytics_models_description(),
    }


def get_analytics_data(current_tenant: Tenant | None = None, force: bool = False) -> dict[str, Any]:
    current_tenant = current_tenant or get_current_tenant()
    if not current_tenant.analytics_enabled and not force:
        return {}
    data = {
        **get_analytics_apps_data(),
        **get_analytics_models_data(),
    }
    for key in data.keys():
        if key not in current_tenant.analytics_sources:
            del data[key]
    return {
        **data,
        "install_id_hash": sha256(get_install_id().encode()).hexdigest(),
        "tenant_hash": sha256(current_tenant.tenant_uuid.bytes).hexdigest(),
        "version": get_full_version(),
    }
