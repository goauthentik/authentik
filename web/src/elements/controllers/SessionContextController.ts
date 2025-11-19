import type { APIResult } from "#common/api/responses";
import { EVENT_WS_MESSAGE } from "#common/constants";
import { isCausedByAbortError, parseAPIResponseError } from "#common/errors/network";
import { me } from "#common/users";

import { AKConfigMixin, kAKConfig } from "#elements/mixins/config";
import { SessionContext, SessionMixin } from "#elements/mixins/session";
import type { ReactiveElementHost } from "#elements/types";

import { SessionUser } from "@goauthentik/api";

import { setUser } from "@sentry/browser";

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

    #host: ReactiveElementHost<SessionMixin & AKConfigMixin>;
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
        this.#log("Fetching session...");

        this.#abortController?.abort();

        this.#abortController = new AbortController();

        return me({
            signal: this.#abortController.signal,
        })
            .then((session) => {
                const config = this.#host[kAKConfig];

                if (config?.errorReporting.sendPii) {
                    console.debug("authentik/config: Sentry with PII enabled.");

                    setUser({ email: session.user.email });
                }

                console.debug("authentik/controller/session: Fetched session", session);
                this.#context.setValue(session);
                this.#host.session = session;
            })
            .catch(async (error: unknown) => {
                if (isCausedByAbortError(error)) {
                    this.#log("Aborted fetching session");
                    return;
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
        window.addEventListener(EVENT_WS_MESSAGE, this.#fetch);
        this.#fetch();
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_WS_MESSAGE, this.#fetch);
        this.#abortController?.abort();
    }
}
