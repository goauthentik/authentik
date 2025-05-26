import { AKConfigMixin } from "#elements/mixins/config";
import { createMixin } from "@goauthentik/elements/types";

import { CapabilitiesEnum } from "@goauthentik/api";

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
 * A mixin that provides the capability methods to the element.
 *
 * Usage:
 *
 * After importing, simply mixin this function:
 *
 * ```ts
 * export class AkMyNiftyNewFeature extends WithCapabilitiesConfig(AKElement) {
 * }
 * ```
 *
 * And then if you need to check on a capability:
 *
 * ```ts
 * if (this.can(CapabilitiesEnum.IsEnterprise)) { ... }
 * ```
 *
 *
 * Passing `true` as the second mixin argument
 *
 * @category Mixin
 *
 */
export const WithCapabilitiesConfig = createMixin<CapabilitiesMixin, AKConfigMixin>(
    ({ SuperClass }) => {
        abstract class CapabilitiesProvider extends SuperClass implements CapabilitiesMixin {
            public can(capability: CapabilitiesEnum) {
                const config = this.authentikConfig;

                if (!config) {
                    throw new Error(
                        `ConfigContext: Attempted to check capability "${capability}" before initialization. Does the element have the AuthentikConfigMixin applied?`,
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
