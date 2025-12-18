import type { APIResult } from "#common/api/responses";
import { isCausedByAbortError, parseAPIResponseError } from "#common/errors/network";

import { AKConfigMixin } from "#elements/mixins/config";
import { type LocaleMixin } from "#elements/mixins/locale";
import { SessionContext, SessionMixin } from "#elements/mixins/session";
import type { ReactiveElementHost } from "#elements/types";

import { SessionUser } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

/**
 * A controller that provides the session information to the element.
 *
 * @see {@linkcode SessionMixin}
 */
export class SessionContextController implements ReactiveController {
    #log = console.debug.bind(console, `authentik/controller/session`);
    #abortController: null | AbortController = null;

    #host: ReactiveElementHost<LocaleMixin & SessionMixin & AKConfigMixin>;
    #context: ContextProvider<SessionContext>;

    constructor(
        host: ReactiveElementHost<SessionMixin & AKConfigMixin>,
        initialValue?: APIResult<SessionUser>,
    ) {
        this.#host = host;

        this.#context = new ContextProvider(this.#host, {
            context: SessionContext,
            initialValue: initialValue ?? { loading: true, error: null },
        });
    }

    #fetch = () => {
        if (!this.#host.refreshSession) {
            this.#log("No refreshSession method available, skipping session fetch");
            return Promise.resolve();
        }

        this.#abortController?.abort();

        this.#abortController = new AbortController();

        return this.#host
            .refreshSession({
                signal: this.#abortController.signal,
            })
            .then((session) => {
                this.#context.setValue(session);
                this.#host.requestUpdate?.();
            })
            .catch(async (error: unknown) => {
                if (isCausedByAbortError(error)) {
                    this.#log("Aborted fetching session");
                }

                const parsedError = parseAPIResponseError(error);
                console.error("authentik/controller/session: Failed to fetch session", parsedError);

                throw error;
            })
            .finally(() => {
                this.#abortController = null;
            });
    };

    public hostConnected() {
        this.#fetch();
    }

    public hostDisconnected() {
        this.#context.clearCallbacks();
        this.#abortController?.abort();
    }
}
