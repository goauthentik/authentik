import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { isCausedByAbortError } from "#common/errors/network";

import { AKConfigMixin, AuthentikConfigContext, kAKConfig } from "#elements/mixins/config";
import type { ReactiveElementHost } from "#elements/types";

import { Config, RootApi } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

/**
 * A controller that provides the application configuration to the element.
 */
export class ConfigContextController implements ReactiveController {
    #log = console.debug.bind(console, `authentik/controller/config`);
    #abortController: null | AbortController = null;

    #host: ReactiveElementHost<AKConfigMixin>;
    #context: ContextProvider<AuthentikConfigContext>;

    constructor(host: ReactiveElementHost<AKConfigMixin>, initialValue: Config) {
        this.#host = host;

        this.#context = new ContextProvider(this.#host, {
            context: AuthentikConfigContext,
            initialValue,
        });

        this.#host[kAKConfig] = initialValue;
    }

    #fetch = () => {
        this.#log("Fetching configuration...");

        this.#abortController?.abort();

        this.#abortController = new AbortController();

        return new RootApi(DEFAULT_CONFIG)
            .rootConfigRetrieve({
                signal: this.#abortController.signal,
            })
            .then((authentikConfig) => {
                this.#context.setValue(authentikConfig);
                this.#host[kAKConfig] = authentikConfig;
            })
            .catch((error: unknown) => {
                if (isCausedByAbortError(error)) {
                    this.#log("Aborted fetching configuration");
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
        // If the Interface changes its config information, we should notify all
        // users of the context of that change, without creating an infinite
        // loop of resets.
        if (this.#host[kAKConfig] && this.#host[kAKConfig] !== this.#context.value) {
            this.#context.setValue(this.#host[kAKConfig]);
        }
    }
}
