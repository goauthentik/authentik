import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { isCausedByAbortError } from "#common/errors/network";
import { isGuest } from "#common/users";

import { SessionMixin } from "#elements/mixins/session";
import { VersionContext, VersionMixin } from "#elements/mixins/version";
import type { ReactiveElementHost } from "#elements/types";

import { AdminApi, Version } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

export class VersionContextController implements ReactiveController {
    #log = console.debug.bind(console, `authentik/controller/version`);
    #abortController: null | AbortController = null;

    #host: ReactiveElementHost<SessionMixin & VersionMixin>;
    #context: ContextProvider<VersionContext>;

    constructor(host: ReactiveElementHost<VersionMixin & VersionMixin>, initialValue?: Version) {
        this.#host = host;
        this.#context = new ContextProvider(this.#host, {
            context: VersionContext,
            initialValue,
        });
    }

    #fetch = () => {
        this.#log("Fetching latest version...");

        this.#abortController = new AbortController();

        return new AdminApi(DEFAULT_CONFIG)
            .adminVersionRetrieve({
                signal: this.#abortController.signal,
            })
            .then((version) => {
                this.#context.setValue(version);
                this.#host.version = version;
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
        window.addEventListener(EVENT_REFRESH, this.#refreshListener);
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH, this.#refreshListener);
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
