import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { isAbortError } from "#common/errors/network";
import { VersionContext, VersionMixin } from "#elements/mixins/version";
import type { ReactiveElementHost } from "#elements/types";

import { Context, ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

import { AdminApi, Version } from "@goauthentik/api";

export class VersionContextController implements ReactiveController {
    #log = console.debug.bind(console, `authentik/controller/version`);
    #abortController: null | AbortController = null;

    #host: ReactiveElementHost<VersionMixin>;
    #context: ContextProvider<Context<unknown, Version>>;

    constructor(host: ReactiveElementHost<VersionMixin>, initialValue?: Version) {
        this.#host = host;
        this.#context = new ContextProvider(this.#host, {
            context: VersionContext,
            initialValue,
        });
    }

    #fetch = () => {
        this.#log("Fetching latest version...");

        this.#abortController?.abort();

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
        window.addEventListener(EVENT_REFRESH, this.#fetch);
        this.#fetch();
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH, this.#fetch);
        this.#abortController?.abort();
    }

    public hostUpdate() {
        // If the Interface changes its version information for some reason,
        // we should notify all users of the context of that change. doesn't
        if (this.#host.version && this.#host.version !== this.#context.value) {
            this.#context.setValue(this.#host.version);
        }
    }
}
