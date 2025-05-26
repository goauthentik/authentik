import { createMixin } from "#elements/types";

import { consume, createContext } from "@lit/context";
import { state } from "lit/decorators.js";

import type { Version } from "@goauthentik/api";

/**
 * The Lit context for application branding.
 *
 * @category Context
 * @see {@linkcode VersionMixin}
 * @see {@linkcode WithVersion}
 */

export const VersionContext = createContext<Version>(Symbol.for("authentik-version-context"));

/**
 * A mixin that provides the current version to the element.
 *
 * @see {@linkcode WithVersion}
 */
export interface VersionMixin {
    /**
     * The current version of the application.
     *
     * @format semver
     */
    readonly version: Version;
}

/**
 * A mixin that provides the current authentik version to the element.
 *
 * @category Mixin
 *
 * @see {@link https://lit.dev/docs/composition/mixins/#mixins-in-typescript | Lit Mixins}
 */
export const WithVersion = createMixin<VersionMixin>(
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
        abstract class VersionProvider extends SuperClass implements VersionMixin {
            @consume({
                context: VersionContext,
                subscribe,
            })
            @state()
            public version!: Version;
        }

        return VersionProvider;
    },
);
