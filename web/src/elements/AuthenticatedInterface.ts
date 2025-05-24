import { LicenseContextController } from "#elements/Interface/EnterpriseContextController";
import { VersionContextController } from "#elements/Interface/VersionContextController";
import { Interface } from "@goauthentik/elements/Interface";

export class AuthenticatedInterface extends Interface {
    constructor() {
        super();

        this.addController(new LicenseContextController(this));
        this.addController(new VersionContextController(this));
    }
}
