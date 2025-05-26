import { createMixin } from "@goauthentik/elements/types";

import { consume, createContext } from "@lit/context";

import type { Config } from "@goauthentik/api";

/**
 * The Lit context for the application configuration.
 *
 * @category Context
 * @see {@linkcode AKConfigMixin}
 * @see {@linkcode WithAuthentikConfig}
 */
export const AuthentikConfigContext = createContext<Config>(Symbol.for("authentik-config-context"));

/**
 * A consumer that provides the application configuration to the element.
 *
 * @category Mixin
 * @see {@linkcode WithAuthentikConfig}
 */
export interface AKConfigMixin {
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
export const WithAuthentikConfig = createMixin<AKConfigMixin>(
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
        abstract class AKConfigProvider extends SuperClass implements AKConfigMixin {
            @consume({
                context: AuthentikConfigContext,
                subscribe,
            })
            public readonly authentikConfig!: Readonly<Config>;
        }

        return AKConfigProvider;
    },
);
