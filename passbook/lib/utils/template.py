"""passbook lib template utilities"""
from django.template import Context, loader


def render_to_string(template_path: str, ctx: Context) -> str:
    """Render a template to string"""
    template = loader.get_template(template_path)
    return template.render(ctx)
