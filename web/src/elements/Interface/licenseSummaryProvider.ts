import { authentikEnterpriseContext } from "@goauthentik/elements/AuthentikContexts";
import { Constructor } from "@goauthentik/elements/types.js";

import { consume } from "@lit/context";
import type { LitElement } from "lit";

import { type LicenseSummary, LicenseSummaryStatusEnum } from "@goauthentik/api";

export function WithLicenseSummary<T extends Constructor<LitElement>>(
    superclass: T,
    subscribe = true,
) {
    abstract class WithEnterpriseProvider extends superclass {
        @consume({ context: authentikEnterpriseContext, subscribe })
        public licenseSummary!: LicenseSummary;

        get hasEnterpriseLicense() {
            return this.licenseSummary?.status !== LicenseSummaryStatusEnum.Unlicensed;
        }
    }

    return WithEnterpriseProvider;
}
