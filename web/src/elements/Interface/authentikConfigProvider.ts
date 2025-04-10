import { authentikConfigContext } from "@goauthentik/elements/AuthentikContexts";
import { createMixin } from "@goauthentik/elements/types";

import { consume } from "@lit/context";

import type { Config } from "@goauthentik/api";

/**
 * A consumer that provides the application configuration to the element.
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
                context: authentikConfigContext,
                subscribe,
            })
            public readonly authentikConfig!: Readonly<Config>;
        }

        return AKConfigProvider;
    },
);
