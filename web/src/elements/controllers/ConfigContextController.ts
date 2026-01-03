import { DEFAULT_CONFIG } from "#common/api/config";

import { ReactiveContextController } from "#elements/controllers/ReactiveContextController";
import { AKConfigMixin, AuthentikConfigContext, kAKConfig } from "#elements/mixins/config";
import type { ReactiveElementHost } from "#elements/types";

import { Config, RootApi } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";

/**
 * A controller that provides the application configuration to the element.
 */
export class ConfigContextController extends ReactiveContextController<Config> {
    protected static override logPrefix = "config";

    #host: ReactiveElementHost<AKConfigMixin>;
    #context: ContextProvider<AuthentikConfigContext>;

    constructor(host: ReactiveElementHost<AKConfigMixin>, initialValue: Config) {
        super();
        this.#host = host;

        this.#context = new ContextProvider(this.#host, {
            context: AuthentikConfigContext,
            initialValue,
        });

        this.#host[kAKConfig] = initialValue;
    }

    protected apiEndpoint(requestInit?: RequestInit) {
        return new RootApi(DEFAULT_CONFIG).rootConfigRetrieve(requestInit);
    }

    protected doRefresh(authentikConfig: Config) {
        this.#context.setValue(authentikConfig);
        this.#host[kAKConfig] = authentikConfig;
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
