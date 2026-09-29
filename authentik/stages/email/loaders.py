"""Database template loader for email templates"""

from functools import cache

from django.template import Context, Engine, Origin, TemplateDoesNotExist
from django.template.backends.django import get_installed_libraries
from django.template.loaders.base import Loader


class EmailTemplateLoader(Loader):
    """Resolve extends/includes with EmailTemplate rows"""

    def get_template_sources(self, template_name: str):
        yield Origin(name=f"custom:{template_name}", template_name=template_name, loader=self)
        yield Origin(name=f"managed:{template_name}", template_name=template_name, loader=self)

    def get_contents(self, origin: Origin) -> str:
        from authentik.stages.email.models import EmailTemplate

        custom = origin.name.startswith("custom:")
        template = EmailTemplate.objects.filter(
            path=origin.template_name, managed__isnull=custom
        ).first()
        if not template:
            raise TemplateDoesNotExist(origin)
        return template.body


@cache
def email_engine() -> Engine:
    return Engine(
        loaders=["authentik.stages.email.loaders.EmailTemplateLoader"],
        libraries=get_installed_libraries(),
    )


def render_email_template(body: str, context: dict | None) -> str:
    return email_engine().from_string(body).render(Context(context or {}))
