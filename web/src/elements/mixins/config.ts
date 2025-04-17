import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import type { ReactiveElementHost } from "@goauthentik/elements/types.js";
import { createMixin } from "@goauthentik/elements/utils/mixins";
import { ThemedElement } from "@goauthentik/elements/utils/theme";

import { consume, createContext } from "@lit/context";
import { Context, ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

import type { Config } from "@goauthentik/api";
import { RootApi } from "@goauthentik/api";

export const authentikConfigContext = createContext<Config>(Symbol("authentik-config-context"));

export class ConfigController implements ReactiveController {
    readonly #host: ReactiveElementHost<ThemedElement>;
    readonly #context: ContextProvider<Context<unknown, Config | undefined>>;

    constructor(host: ReactiveElementHost<ThemedElement>) {
        const { config } = globalAK();

        this.#host = host;

        this.#context = new ContextProvider(this.#host, {
            context: authentikConfigContext,
            // Pre-hydrate from template-embedded config.
            initialValue: config,
        });

        this.#host.config = config;

        this.refresh();
    }

    public readonly refresh = () => {
        return new RootApi(DEFAULT_CONFIG).rootConfigRetrieve().then((config) => {
            this.#context.setValue(config);
            this.#host.config = config;
        });
    };

    public hostConnected() {
        window.addEventListener(EVENT_REFRESH, this.refresh);
    }

    public hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH, this.refresh);
    }

    public hostUpdate() {
        // If the Interface changes its config information, we should notify all
        // users of the context of that change, without creating an infinite
        // loop of resets.

        if (this.#host.config !== this.#context.value) {
            this.#context.setValue(this.#host.config);
        }
    }
}

/**
 * A consumer that provides the application configuration to the element.
 */
export interface ConfigConsumer {
    /**
     * The current configuration of the application.
     */
    readonly authentikConfig: Readonly<Config>;
}

/**
 * A mixin that provides the application configuration to the element.
 *
 * @category Mixin
 */
export const WithAuthentikConfig = createMixin<ConfigConsumer>(
    ({
        /**
         * The superclass constructor to extend.
         */
        SuperClass,
        /**
         * Whether or not to subscribe to the context.
         */
        subscribe = true,
    }) => {
        abstract class AKConfigProvider extends SuperClass implements ConfigConsumer {
            @consume({
                context: authentikConfigContext,
                subscribe,
            })
            public readonly authentikConfig!: Readonly<Config>;
        }

        return AKConfigProvider;
    },
);
