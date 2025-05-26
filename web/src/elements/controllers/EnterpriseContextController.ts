import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH_ENTERPRISE } from "#common/constants";
import { isAbortError } from "#common/errors/network";
import { LicenseContext, LicenseMixin } from "#elements/mixins/license";
import type { ReactiveElementHost } from "#elements/types";

import { Context, ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

import { EnterpriseApi, LicenseSummary } from "@goauthentik/api";

export class LicenseContextController implements ReactiveController {
    #log = console.debug.bind(console, `authentik/controller/license`);
    #abortController: null | AbortController = null;

    #host: ReactiveElementHost<LicenseMixin>;
    #context: ContextProvider<Context<unknown, LicenseSummary>>;

    constructor(host: ReactiveElementHost<LicenseMixin>, initialValue?: LicenseSummary) {
        this.#host = host;
        this.#context = new ContextProvider(this.#host, {
            context: LicenseContext,
            initialValue: initialValue,
        });
    }

    #fetch = () => {
        this.#log("Fetching license summary...");

        this.#abortController?.abort();

        this.#abortController = new AbortController();

        return new EnterpriseApi(DEFAULT_CONFIG)
            .enterpriseLicenseSummaryRetrieve(
                {},
                {
                    signal: this.#abortController.signal,
                },
            )
            .then((enterprise) => {
                this.#context.setValue(enterprise);
                this.#host.licenseSummary = enterprise;
            })

            .catch((error: unknown) => {
                if (isAbortError(error)) {
                    this.#log("Aborted fetching license summary");
                    return;
                }

                throw error;
            })
            .finally(() => {
                this.#abortController = null;
            });
    };

    public hostConnected() {
        window.addEventListener(EVENT_REFRESH_ENTERPRISE, this.#fetch);
        this.#fetch();
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH_ENTERPRISE, this.#fetch);
        this.#abortController?.abort();
    }

    public hostUpdate() {
        // If the Interface changes its config information, we should notify all
        // users of the context of that change, without creating an infinite
        // loop of resets.
        if (this.#host.licenseSummary && this.#host.licenseSummary !== this.#context.value) {
            this.#context.setValue(this.#host.licenseSummary);
        }
    }
}
