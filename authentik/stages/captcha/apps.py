"""authentik captcha app"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStageCaptchaConfig(ManagedAppConfig):
    """authentik captcha app"""

    name = "authentik.stages.captcha"
    label = "authentik_stages_captcha"
    verbose_name = "authentik Stages.Captcha"
    default = True
