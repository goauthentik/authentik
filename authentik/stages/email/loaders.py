"""Database template loader for email templates"""

from functools import cache

from django.template import Context, Engine, Origin, Template, TemplateDoesNotExist
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


def render_email_template(body: str, path: str, context: dict | None, managed: bool = False) -> str:
    return compile_email_template(body, path, managed).render(Context(context or {}))


def compile_email_template(body: str, path: str, managed: bool = False) -> Template:
    engine = email_engine()
    origin = Origin(
        name=f"{'managed' if managed else 'custom'}:{path}",
        template_name=path,
        loader=engine.template_loaders[0],
    )
    return Template(body, origin=origin, engine=engine)
