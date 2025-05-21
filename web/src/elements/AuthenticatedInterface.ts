import { Interface } from "#elements/Interface";
import { LicenseContextController } from "#elements/Interface/EnterpriseContextController";
import { VersionContextController } from "#elements/Interface/VersionContextController";

export class AuthenticatedInterface extends Interface {
    constructor() {
        super();

        this.addController(new LicenseContextController(this));
        this.addController(new VersionContextController(this));
    }
}
