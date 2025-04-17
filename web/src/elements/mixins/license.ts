import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH_ENTERPRISE } from "@goauthentik/common/constants";
import type { ReactiveElementHost } from "@goauthentik/elements/types.js";
import { createMixin } from "@goauthentik/elements/utils/mixins";

import { Context, ContextProvider, createContext } from "@lit/context";
import { consume } from "@lit/context";
import type { ReactiveController } from "lit";

import type { LicenseSummary } from "@goauthentik/api";
import { EnterpriseApi } from "@goauthentik/api";
import { LicenseSummaryStatusEnum } from "@goauthentik/api";

/**
 * A consumer that provides license information to the element.
 */
export interface LicenseConsumer {
    /**
     * Summary of the current license.
     */
    licenseSummary?: LicenseSummary;
}

/**
 * Predicate if the current license is an enterprise license.
 * @param license License summary to check
 */
export function isEnterpriseLicense(license?: LicenseSummary): boolean {
    return license?.status !== LicenseSummaryStatusEnum.Unlicensed;
}

export const authentikEnterpriseContext = createContext<LicenseSummary>(
    Symbol("authentik-enterprise-context"),
);

export class LicenseController implements ReactiveController {
    readonly #host: ReactiveElementHost<LicenseConsumer>;
    readonly #context: ContextProvider<Context<unknown, LicenseSummary | undefined>>;

    constructor(host: ReactiveElementHost<LicenseConsumer>) {
        this.#host = host;

        this.#context = new ContextProvider(this.#host, {
            context: authentikEnterpriseContext,
            initialValue: undefined,
        });

        this.refresh();
    }

    public refresh = () => {
        return new EnterpriseApi(DEFAULT_CONFIG)
            .enterpriseLicenseSummaryRetrieve()
            .then((licenseSummary) => {
                this.#context.setValue(licenseSummary);

                this.#host.licenseSummary = licenseSummary;
            });
    };

    public hostConnected() {
        window.addEventListener(EVENT_REFRESH_ENTERPRISE, this.refresh);
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH_ENTERPRISE, this.refresh);
    }

    public hostUpdate() {
        // If the Interface changes its config information, we should notify all
        // users of the context of that change, without creating an infinite
        // loop of resets.
        if (this.#host.licenseSummary !== this.#context.value) {
            this.#context.setValue(this.#host.licenseSummary);
        }
    }
}

/**
 * A mixin that provides the license information to the element.
 */
export const WithLicenseSummary = createMixin<LicenseConsumer>(
    ({ SuperClass, subscribe = true }) => {
        abstract class LicenseProvider extends SuperClass implements LicenseConsumer {
            @consume({
                context: authentikEnterpriseContext,
                subscribe,
            })
            public readonly licenseSummary!: LicenseSummary;
        }

        return LicenseProvider;
    },
);
