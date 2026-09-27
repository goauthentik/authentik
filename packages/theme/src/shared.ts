/**
 * @file Styleframe instance and shared primitives for the authentik theme.
 *   This module configures one global {@link Styleframe} instance and re-exports
 *   its primitives ({@link variable}, {@link theme}, {@link ref}, {@link selector},
 *   etc.) for use by the per-category token modules under `./authentik/`.
 *   The instance is configured so that:
 *
 *   - Variable names use the `--ak-*` prefix authentik components and brand custom CSS expect. Source
 *     tokens are written in dot-notation (`color.primary`) and the configured name function
 *     rewrites that to `ak-color-primary` before styleframe prepends the leading `--`.
 *   - Tokens authored under `pf-global.*` pass through unprefixed, so the PatternFly bridge in
 *     `./patternfly/` emits `--pf-global--*` names rather than `--ak-global--pf-global--*`.
 *   - The theme selector matches the existing `html[data-theme="..."]` convention used across the
 *     authentik stylesheets.
 */

import { createUseVariable } from "@styleframe/theme";
import { defaultVariableNameFn } from "@styleframe/transpiler";
import { styleframe, type StyleframeOptions } from "styleframe";

/**
 * Authentik-specific styleframe configuration.
 */
export const authentikStyleframeOptions: StyleframeOptions = {
    indent: "    ",
    variables: {
        name: ({ name }: { name: string }) =>
            name.startsWith("pf-global.")
                ? defaultVariableNameFn({ name })
                : defaultVariableNameFn({ name: `ak-global.${name}` }),
    },
    themes: {
        selector: ({ name }: { name: string }) => `html[data-theme="${name}"]`,
    },
};

/**
 * Singleton styleframe instance used by every token module.
 */
export const instance = styleframe(authentikStyleframeOptions);

export const createPfGlobal = (category: string) => createUseVariable(`pf-global.${category}`);

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
