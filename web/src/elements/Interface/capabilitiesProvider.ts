import { authentikConfigContext } from "@goauthentik/elements/AuthentikContexts";
import { createMixin } from "@goauthentik/elements/types";

import { consume } from "@lit/context";

import { CapabilitiesEnum } from "@goauthentik/api";
import { Config } from "@goauthentik/api";

/**
 * A consumer that provides the capability methods to the element.
 *
 */
export interface CapabilitiesMixin {
    /**
     * Predicate to determine if the current user has a given capability.
     */
    can(
        /**
         * The capability enum to check.
         */
        capability: CapabilitiesEnum,
    ): boolean;
}

/**
 * Lexically-scoped symbol for the capabilities configuration.
 *
 * @internal
 */
const kCapabilitiesConfig: unique symbol = Symbol("capabilitiesConfig");

/**
 * A mixin that provides the capability methods to the element.
 *
 * Usage:
 *
 * After importing, simply mixin this function:
 *
 * ```ts
 * export class AkMyNiftyNewFeature extends withCapabilitiesContext(AKElement) {
 * }
 * ```
 *
 * And then if you need to check on a capability:
 *
 * ```ts
 * if (this.can(CapabilitiesEnum.IsEnterprise) { ... }
 * ```
 *
 *
 * Passing `true` as the second mixin argument
 *
 * @category Mixin
 *
 */
export const WithCapabilitiesConfig = createMixin<CapabilitiesMixin>(
    ({ SuperClass, subscribe = true }) => {
        abstract class CapabilitiesProvider extends SuperClass implements CapabilitiesMixin {
            @consume({
                context: authentikConfigContext,
                subscribe,
            })
            private readonly [kCapabilitiesConfig]: Config | undefined;

            public can(capability: CapabilitiesEnum) {
                const config = this[kCapabilitiesConfig];

                if (!config) {
                    throw new Error(
                        "ConfigContext: Attempted to access site configuration before initialization.",
                    );
                }

                return config.capabilities.includes(capability);
            }
        }

        return CapabilitiesProvider;
    },
);

// Re-export `CapabilitiesEnum`, so you won't have to import it on a separate line if you
// don't need anything else from the API.

export { CapabilitiesEnum };
