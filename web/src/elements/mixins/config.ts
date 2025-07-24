import { createMixin } from "#elements/types";

import type { Config } from "@goauthentik/api";

import { consume, Context, createContext } from "@lit/context";

export const kAKConfig = Symbol("kAKConfig");

/**
 * The Lit context for the application configuration.
 *
 * @category Context
 * @see {@linkcode AKConfigMixin}
 * @see {@linkcode WithAuthentikConfig}
 */
export const AuthentikConfigContext = createContext<Config>(Symbol.for("authentik-config-context"));

export type AuthentikConfigContext = Context<symbol, Config>;

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
    readonly [kAKConfig]: Readonly<Config>;
}

/**
 * A mixin that provides the application configuration to the element.
 *
 * @category Mixin
 */
export const WithAuthentikConfig = createMixin<AKConfigMixin>(
    ({
        // ---
        SuperClass,
        subscribe = true,
    }) => {
        abstract class AKConfigProvider extends SuperClass implements AKConfigMixin {
            @consume({
                context: AuthentikConfigContext,
                subscribe,
            })
            public readonly [kAKConfig]!: Readonly<Config>;
        }

        return AKConfigProvider;
    },
);
