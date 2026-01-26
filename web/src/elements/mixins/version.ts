import { createMixin } from "#elements/types";

import type { Version } from "@goauthentik/api";

import { consume, createContext } from "@lit/context";
import { property } from "lit/decorators.js";

/**
 * The Lit context for authentik's version.
 *
 * @category Context
 * @see {@linkcode VersionMixin}
 * @see {@linkcode WithVersion}
 */

export const VersionContext = createContext<Version | null>(Symbol("authentik-version-context"));

export type VersionContext = typeof VersionContext;

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
    readonly version: Version | null;
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
            @property({ attribute: false })
            public version: Version | null = null;
        }

        return VersionProvider;
    },
);
