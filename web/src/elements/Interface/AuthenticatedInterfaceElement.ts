import { LicenseController } from "@goauthentik/elements/mixins/license";
import { SessionController } from "@goauthentik/elements/mixins/session";
import { VersionController } from "@goauthentik/elements/mixins/version";
import { ThemedElement } from "@goauthentik/elements/utils/theme";

import { state } from "lit/decorators.js";

import type { LicenseSummary, Version } from "@goauthentik/api";

import { InterfaceElement } from "./InterfaceElement.js";

/**
 * A UI interface representing an  authenticated entry point within the application.
 */
export abstract class AuthenticatedInterfaceElement
    extends InterfaceElement
    implements ThemedElement
{
    @state()
    licenseSummary?: LicenseSummary;

    @state()
    version?: Version;

    public override registerControllers() {
        super.registerControllers();
        new LicenseController(this);
        new VersionController(this);
        new SessionController(this);
    }
}
