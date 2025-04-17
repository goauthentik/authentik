import { LicenseController } from "@goauthentik/elements/mixins/license";
import { SessionController } from "@goauthentik/elements/mixins/session";
import { VersionController } from "@goauthentik/elements/mixins/version";
import { ThemedElement } from "@goauthentik/elements/utils/theme";

import { state } from "lit/decorators.js";

import type { LicenseSummary, Version } from "@goauthentik/api";

import { InterfaceElement } from "./InterfaceElement.js";

export interface AuthenticatedInterfaceElement extends ThemedElement {
    licenseSummary?: LicenseSummary;
    version?: Version;
}

export abstract class AKAuthenticatedInterfaceElement
    extends InterfaceElement
    implements AuthenticatedInterfaceElement
{
    @state()
    licenseSummary?: LicenseSummary;

    @state()
    version?: Version;

    constructor(init?: AuthenticatedInterfaceElement) {
        super(init);
    }

    public override registerControllers() {
        super.registerControllers();
        new LicenseController(this);
        new VersionController(this);
        new SessionController(this);
    }
}
