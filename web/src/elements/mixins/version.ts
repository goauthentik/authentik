import { createMixin } from "#elements/types";

import type { Version } from "@goauthentik/api";

import { Context, consume, createContext } from "@lit/context";

/**
 * The Lit context for application branding.
 *
 * @category Context
 * @see {@linkcode VersionMixin}
 * @see {@linkcode WithVersion}
 */

export const VersionContext = createContext<Version>(Symbol.for("authentik-version-context"));

export type VersionContext = Context<symbol, Version>;

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
 */
export const WithVersion = createMixin<VersionMixin>(
    ({
        // ---
        SuperClass,
        subscribe = true,
    }) => {
        abstract class VersionProvider extends SuperClass implements VersionMixin {
            @consume({
                context: VersionContext,
                subscribe,
            })
            public version!: Version;
        }

        return VersionProvider;
    },
);
