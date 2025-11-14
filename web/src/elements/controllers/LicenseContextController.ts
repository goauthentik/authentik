import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH_ENTERPRISE } from "#common/constants";
import { isCausedByAbortError } from "#common/errors/network";
import { isGuest } from "#common/users";

import { LicenseContext, LicenseMixin } from "#elements/mixins/license";
import { SessionMixin } from "#elements/mixins/session";
import type { ReactiveElementHost } from "#elements/types";

import { EnterpriseApi, LicenseSummary } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

export class LicenseContextController implements ReactiveController {
    #log = console.debug.bind(console, `authentik/controller/license`);
    #abortController: null | AbortController = null;

    #host: ReactiveElementHost<SessionMixin & LicenseMixin>;
    #context: ContextProvider<LicenseContext>;

    constructor(host: ReactiveElementHost<LicenseMixin>, initialValue?: LicenseSummary) {
        this.#host = host;
        this.#context = new ContextProvider(this.#host, {
            context: LicenseContext,
            initialValue: initialValue,
        });
    }

    #fetch = () => {
        this.#log("Fetching license summary...");

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
                if (isCausedByAbortError(error)) {
                    this.#log("Aborted fetching license summary");
                    return;
                }

                throw error;
            })
            .finally(() => {
                this.#abortController = null;
            });
    };

    #refreshListener = (event: Event) => {
        this.#abortController?.abort(event.type);
        this.#fetch();
    };

    public hostConnected() {
        window.addEventListener(EVENT_REFRESH_ENTERPRISE, this.#refreshListener);
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH_ENTERPRISE, this.#refreshListener);
    }

    public hostUpdate() {
        const { currentUser } = this.#host;

        if (currentUser && !isGuest(currentUser) && !this.#abortController) {
            this.#fetch();

            return;
        }

        if (!currentUser && this.#abortController) {
            this.#abortController.abort("session-invalidated");
        }
    }
}
