"""duo tasks"""

from dramatiq.actor import actor
from structlog.stdlib import get_logger

from authentik.core.models import User
from authentik.stages.authenticator_duo.models import AuthenticatorDuoStage, DuoDevice

LOGGER = get_logger()


@actor(store_results=True)
def duo_import_devices(stage_pk: str):
    """Import duo devices"""
    created = 0
    stage: AuthenticatorDuoStage = AuthenticatorDuoStage.objects.filter(pk=stage_pk).first()
    if not stage:
        LOGGER.info("No stage found", pk=stage_pk)
        return {"error": "No stage found", "count": created}
    if stage.admin_integration_key == "":
        LOGGER.info("Stage does not have admin integration configured", stage=stage)
        return {"error": "Stage does not have admin integration configured", "count": created}
    client = stage.admin_client()
    try:
        for duo_user in client.get_users_iterator():
            user_id = duo_user.get("user_id")
            username = duo_user.get("username")

            user = User.objects.filter(username=username).first()
            if not user:
                LOGGER.debug("User not found", username=username)
                continue
            device = DuoDevice.objects.filter(duo_user_id=user_id, user=user, stage=stage).first()
            if device:
                LOGGER.debug("User already has a device with ID", id=user_id)
                continue
            DuoDevice.objects.create(
                duo_user_id=user_id,
                user=user,
                stage=stage,
                name="Imported Duo Authenticator",
            )
            created += 1
        return {"error": "", "count": created}
    except RuntimeError as exc:
        LOGGER.warning("failed to get users from duo", exc=exc)
        return {"error": str(exc), "count": created}
