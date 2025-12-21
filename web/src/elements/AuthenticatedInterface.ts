import { LicenseContextController } from "#elements/controllers/LicenseContextController";
import { SessionContextController } from "#elements/controllers/SessionContextController";
import { VersionContextController } from "#elements/controllers/VersionContextController";
import { Interface } from "#elements/Interface";

export class AuthenticatedInterface extends Interface {
    constructor() {
        super();

        this.addController(new LicenseContextController(this));
        this.addController(new SessionContextController(this));
        this.addController(new VersionContextController(this));
    }
}
