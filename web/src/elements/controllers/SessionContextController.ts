import type { APIResult } from "#common/api/responses";
import { createSyntheticGenericError } from "#common/errors/network";

import { ReactiveContextController } from "#elements/controllers/ReactiveContextController";
import { AKConfigMixin } from "#elements/mixins/config";
import { type LocaleMixin } from "#elements/mixins/locale";
import { SessionContext, SessionMixin } from "#elements/mixins/session";
import type { ReactiveElementHost } from "#elements/types";

import { SessionUser } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";

/**
 * A controller that provides the session information to the element.
 *
 * @see {@linkcode SessionMixin}
 */
export class SessionContextController extends ReactiveContextController<APIResult<SessionUser>> {
    protected static override logPrefix = "session";

    #host: ReactiveElementHost<LocaleMixin & SessionMixin & AKConfigMixin>;
    #context: ContextProvider<SessionContext>;

    constructor(
        host: ReactiveElementHost<SessionMixin & AKConfigMixin>,
        initialValue?: APIResult<SessionUser>,
    ) {
        super();

        this.#host = host;

        this.#context = new ContextProvider(this.#host, {
            context: SessionContext,
            initialValue: initialValue ?? { loading: true, error: null },
        });
    }

    protected apiEndpoint(requestInit?: RequestInit) {
        if (!this.#host.refreshSession) {
            // This situation is unlikely, but possible if a host reference becomes
            // stale or is misconfigured.

            this.debug(
                "No `refreshSession` method available, skipping session fetch. Check if the `SessionMixin` is applied correctly.",
            );

            const result: APIResult<SessionUser> = {
                loading: false,
                error: createSyntheticGenericError("No `refreshSession` method available"),
            };

            return Promise.resolve(result);
        }

        return this.#host.refreshSession(requestInit);
    }

    protected doRefresh(session: APIResult<SessionUser>) {
        this.#context.setValue(session);
        this.#host.requestUpdate?.();
    }

    public override hostConnected() {
        this.refresh();
    }

    public override hostDisconnected() {
        this.#context.clearCallbacks();

        super.hostDisconnected();
    }
}
