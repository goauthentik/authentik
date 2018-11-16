"""passbook lib template utilities"""
from django.template import Context, Template, loader


def render_from_string(template: str, ctx: Context) -> str:
    """Render template from string to string"""
    template = Template(template)
    return template.render(ctx)


def render_to_string(template_path: str, ctx: Context) -> str:
    """Render a template to string"""
    template = loader.get_template(template_path)
    return template.render(ctx)
