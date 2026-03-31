import { LicenseContextController } from "#elements/controllers/LicenseContextController";
import { NotificationsContextController } from "#elements/controllers/NotificationsContextController";
import { SessionContextController } from "#elements/controllers/SessionContextController";
import { VersionContextController } from "#elements/controllers/VersionContextController";
import { Interface } from "#elements/Interface";
import { LicenseContext } from "#elements/mixins/license";
import { NotificationsContext } from "#elements/mixins/notifications";
import { SessionContext } from "#elements/mixins/session";
import { VersionContext } from "#elements/mixins/version";

export class AuthenticatedInterface extends Interface {
    constructor() {
        super();

        this.addController(new LicenseContextController(this), LicenseContext);
        this.addController(new SessionContextController(this), SessionContext);
        this.addController(new VersionContextController(this), VersionContext);
        this.addController(new NotificationsContextController(this), NotificationsContext);
    }
}
