import { authentikConfigContext } from "@goauthentik/elements/AuthentikContexts";
import type { AbstractConstructor } from "@goauthentik/elements/types.js";

import { consume } from "@lit/context";
import type { LitElement } from "lit";

import { CapabilitiesEnum } from "@goauthentik/api";
import { Config } from "@goauthentik/api";

// Using a unique, lexically scoped, and locally static symbol as the field name for the context
// means that it's inaccessible to any child class looking for it. It's one of the strongest privacy
// guarantees in JavaScript.

class WCC {
    public static readonly capabilitiesConfig: unique symbol = Symbol();
}

/**
 * withCapabilitiesContext mixes in a single method to any LitElement, `can()`, which takes a
 * CapabilitiesEnum and returns true or false.
 *
 * Usage:
 *
 * After importing, simply mixin this function:
 *
 * ```
 * export class AkMyNiftyNewFeature extends withCapabilitiesContext(AKElement) {
 * ```
 *
 * And then if you need to check on a capability:
 *
 * ```
 * if (this.can(CapabilitiesEnum.IsEnterprise) { ... }
 * ```
 *
 * This code re-exports CapabilitiesEnum, so you won't have to import it on a separate line if you
 * don't need anything else from the API.
 *
 * Passing `true` as the second mixin argument will cause the inheriting class to subscribe to the
 * configuration context. Should the context be explicitly reset, all active web components that are
 * currently active and subscribed to the context will automatically have a `requestUpdate()`
 * triggered with the new configuration.
 *
 */

export function WithCapabilitiesConfig<T extends AbstractConstructor<LitElement>>(
    superclass: T,
    subscribe = true,
) {
    abstract class CapabilitiesContext extends superclass {
        @consume({ context: authentikConfigContext, subscribe })
        private [WCC.capabilitiesConfig]!: Config;

        can(c: CapabilitiesEnum) {
            if (!this[WCC.capabilitiesConfig]) {
                throw new Error(
                    "ConfigContext: Attempted to access site configuration before initialization.",
                );
            }
            return this[WCC.capabilitiesConfig].capabilities.includes(c);
        }
    }

    return CapabilitiesContext;
}

export { CapabilitiesEnum };
