"""Inject brand into current request"""

import json
from collections.abc import Callable
from re import search

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.translation import override
from structlog.stdlib import get_logger

from authentik.brands.models import BrandPolicy
from authentik.brands.utils import get_brand_for_request
from authentik.policies.engine import PolicyEngine

LOGGER = get_logger()


class BrandMiddleware:
    """Add current brand to http request"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        locale_to_set = None
        if not hasattr(request, "brand"):
            brand = get_brand_for_request(request)
            request.brand = brand
            locale = brand.default_locale
            if locale != "":
                locale_to_set = locale
        if locale_to_set:
            with override(locale_to_set):
                return self.get_response(request)
        return self.get_response(request)


class BrandPolicyMiddleware:
    """
    Runs policies bound to `BrandPolicy`s. Uses `request.brand` and `request.user`, so this should
    be placed after `BrandMiddleware` and `AuthenticationMiddleware`.
    """

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        # Caching this is probably not worth the hassle. There shouldn't be enough `BrandPolicy`
        # objects in an installation to warrant caching.
        for brand_policy in BrandPolicy.objects.all():
            if request.brand != brand_policy.brand:
                continue
            if not search(brand_policy.path, request.path):
                continue

            engine = PolicyEngine(brand_policy, request.user, request)
            # Using the engine's cache is probably not worth the hassle. Invalidation is too tricky.
            engine.use_cache = False
            engine.build()
            result = engine.result
            if result.passing:
                LOGGER.debug("Brand Policy passed", brand_policy=brand_policy)
            else:
                LOGGER.debug("Brand Policy failed", brand_policy=brand_policy)
                try:
                    data = json.loads(brand_policy.failure_response)
                    return JsonResponse(
                        data, status=brand_policy.failure_http_status_code, safe=False
                    )
                except json.JSONDecodeError:
                    return HttpResponse(
                        brand_policy.failure_response, status=brand_policy.failure_http_status_code
                    )

        return self.get_response(request)
