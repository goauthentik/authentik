import { Interface } from "#elements/Interface";
import { LicenseContextController } from "#elements/controllers/EnterpriseContextController";
import { VersionContextController } from "#elements/controllers/VersionContextController";

export class AuthenticatedInterface extends Interface {
    constructor() {
        super();

        this.addController(new LicenseContextController(this));
        this.addController(new VersionContextController(this));
    }
}
