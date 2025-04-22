import { Interface } from "@goauthentik/elements/Interface/InterfaceElement";
import { VersionContextController } from "@goauthentik/elements/Interface/VersionContextController";

import { state } from "lit/decorators.js";

import type { LicenseSummary, Version } from "@goauthentik/api";

import { EnterpriseContextController } from "./EnterpriseContextController";

const enterpriseContext = Symbol("enterpriseContext");
const versionContext = Symbol("versionContext");

/**
 * A UI interface representing an  authenticated entry point within the application.
 */
export class AuthenticatedInterface extends Interface {
    [enterpriseContext]!: EnterpriseContextController;
    [versionContext]!: VersionContextController;

    @state()
    licenseSummary?: LicenseSummary;

    @state()
    version?: Version;

    constructor() {
        super();
    }

    _initContexts(): void {
        super._initContexts();
        this[enterpriseContext] = new EnterpriseContextController(this);
        this[versionContext] = new VersionContextController(this);
    }
}
