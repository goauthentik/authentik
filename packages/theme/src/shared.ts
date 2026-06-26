/**
 * @file Styleframe instance and shared primitives for the authentik theme.
 *
 * This module configures one global {@link Styleframe} instance and re-exports
 * its primitives ({@link variable}, {@link theme}, {@link ref}, {@link selector},
 * etc.) for use by the per-category token modules under `./tokens/`.
 *
 * The instance is configured so that:
 *
 * - Variable names use the `--ak-*` prefix authentik components and brand custom
 *   CSS expect. Source tokens are written in dot-notation (`color.primary`)
 *   and the configured name function rewrites that to `ak-color-primary` before
 *   styleframe prepends the leading `--`.
 * - The theme selector matches the existing `html[data-theme="..."]` convention
 *   used across the authentik stylesheets.
 *
 */

import { styleframe, type StyleframeOptions } from "styleframe";

/**
 * Authentik-specific styleframe configuration.
 *
 */
export const authentikStyleframeOptions: StyleframeOptions = {
   indent: "    ",
    variables: {
        name: ({ name }: { name: string }) => `ak-${name.replace(/\./g, "-")}`
    },
    themes: {
        selector: ({ name }: { name: string}) => `html[data-theme="${name}"]`,
    },
};

/**
 * Singleton styleframe instance used by every token module.
 *
 * Importing any module under `./tokens/` triggers the side-effects that
 * register variables and themes against this instance.
 *
 * @type {Styleframe}
 */
export const instance = styleframe(authentikStyleframeOptions);

export const {
    variable,
    theme,
    ref,
    selector,
    atRule,
    keyframes,
    media,
    css,
    utility,
    modifier,
    recipe,
} = instance;
