import { authentikEnterpriseContext } from "@goauthentik/elements/AuthentikContexts";

import { consume } from "@lit-labs/context";
import type { LitElement } from "lit";

import type { LicenseSummary } from "@goauthentik/api";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Constructor<T = object> = abstract new (...args: any[]) => T;

export function WithLicenseSummary<T extends Constructor<LitElement>>(
    superclass: T,
    subscribe = true,
) {
    abstract class WithEnterpriseProvider extends superclass {
        @consume({ context: authentikEnterpriseContext, subscribe })
        public licenseSummary!: LicenseSummary;

        get hasEnterpriseLicense() {
            return this.licenseSummary?.hasLicense;
        }
    }

    return WithEnterpriseProvider;
}
