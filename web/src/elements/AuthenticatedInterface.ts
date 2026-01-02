import { LicenseContextController } from "#elements/controllers/LicenseContextController";
import { NotificationsContextController } from "#elements/controllers/NotificationsContextController";
import { SessionContextController } from "#elements/controllers/SessionContextController";
import { VersionContextController } from "#elements/controllers/VersionContextController";
import { Interface } from "#elements/Interface";
import { NotificationsContext } from "#elements/mixins/notifications";
import { SessionContext } from "#elements/mixins/session";

export class AuthenticatedInterface extends Interface {
    constructor() {
        super();

        this.addController(new LicenseContextController(this));
        this.addController(new SessionContextController(this), SessionContext);
        this.addController(new VersionContextController(this));
        this.addController(new NotificationsContextController(this), NotificationsContext);
    }
}
