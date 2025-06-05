import { createMixin } from "#elements/types";

import { type LicenseSummary, LicenseSummaryStatusEnum } from "@goauthentik/api";

import { Context, consume, createContext } from "@lit/context";

export const LicenseContext = createContext<LicenseSummary>(
    Symbol.for("authentik-license-context"),
);

export type LicenseContext = Context<symbol, LicenseSummary>;

/**
 * A consumer that provides license information to the element.
 */
export interface LicenseMixin {
    /**
     * Summary of the current license.
     */
    readonly licenseSummary: LicenseSummary;

    /**
     * Whether or not the current license is an enterprise license.
     */
    readonly hasEnterpriseLicense: boolean;
}

/**
 * A mixin that provides the license information to the element.
 */
export const WithLicenseSummary = createMixin<LicenseMixin>(
    ({
        // ---
        SuperClass,
        subscribe = true,
    }) => {
        abstract class LicenseProvider extends SuperClass implements LicenseMixin {
            @consume({
                context: LicenseContext,
                subscribe,
            })
            public readonly licenseSummary!: LicenseSummary;

            get hasEnterpriseLicense() {
                return this.licenseSummary?.status !== LicenseSummaryStatusEnum.Unlicensed;
            }
        }

        return LicenseProvider;
    },
);
