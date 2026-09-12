/**
 * @file Import organization for oxfmt, ported from the `@goauthentik/prettier-config` import plugin.
 *
 * oxfmt sorts imports with a perfectionist-style algorithm (selectors, modifiers, and ordered
 * `customGroups`) rather than the ordered regex `groupRules` the old `format-imports` plugin used.
 * The configuration below reproduces the previous grouping: side-effect imports first, then Node
 * built-ins, relative paths, each web alias in turn, the remaining internal/`@goauthentik` imports,
 * third-party packages, and finally Lit.
 */

import type { CustomGroupItemConfig, SortGroupItemConfig, SortImportsConfig } from "oxfmt";

/**
 * authentik web import-path aliases that each get their own import group, in display order.
 *
 * Mirrors the `webSubmodules` list in the former `@goauthentik/prettier-config`; an import is matched
 * in either its `#<alias>/…` (package `imports`) or `@goauthentik/<alias>/…` form.
 */
export const WebSubmodules = ["common", "elements", "components", "user", "admin", "flow"] as const;

/**
 * Ordered custom groups. The first definition that matches an import wins, and any custom group
 * outranks every predefined selector — so the side-effect group must come first to keep bare
 * `import "#elements/…"` statements together at the top instead of being pulled into an alias group.
 */
const customGroups: CustomGroupItemConfig[] = [
    // Side-effect imports (`import "x"`) stay together at the top, regardless of their target.
    { groupName: "side-effect", modifiers: ["side_effect"] },

    // One group per web alias, matching both the `#alias/…` and `@goauthentik/alias/…` forms.
    ...WebSubmodules.map(
        (submodule): CustomGroupItemConfig => ({
            groupName: submodule,
            elementNamePattern: [
                `#${submodule}`,
                `#${submodule}/**`,
                `@goauthentik/${submodule}`,
                `@goauthentik/${submodule}/**`,
            ],
        }),
    ),

    // Any other internal subpath import, e.g. `#logger/browser`.
    { groupName: "ak-internal", elementNamePattern: ["#*", "#*/**"] },

    // Any other `@goauthentik/…` package, including the generated `@goauthentik/api` client.
    { groupName: "ak-namespace", elementNamePattern: ["@goauthentik", "@goauthentik/**"] },

    // Lit and its companion packages (`lit`, `lit-html`, `lit/*`, `@lit/*`) always sort last.
    { groupName: "lit", elementNamePattern: ["lit", "lit*", "lit/**", "@lit*", "@lit/**"] },
];

/** The group order; entries combined in a sub-array are sorted together as one block. */
const groups: SortGroupItemConfig[] = [
    "side-effect",
    "builtin",
    // Relative imports (`../`, `./`, `./index`).
    ["parent", "sibling", "index"],
    ...WebSubmodules,
    "ak-internal",
    "ak-namespace",
    "external",
    "lit",
    // Stylesheet imports sort last, matching the former plugin's trailing `\.css$` rule. The
    // `style` selector matches on extension alone, so this covers both the relative
    // (`#common/styles/…css`) and bare-package (`@patternfly/…css`) forms — which is exactly the
    // old behavior, and why `style` must not be listed with the relative imports above.
    "style",
];

/**
 * authentik's oxfmt import-sorting configuration.
 *
 * @remarks
 * `sortSideEffects` is `true` because the former `format-imports` plugin sorted side-effect imports
 * too — every checked-in side-effect block is already in sorted order, and leaving it `false` both
 * deviates from that and makes oxfmt drop the blank line that separates the block from the imports
 * below it.
 *
 * `ignoreCase` is `false` to match the previous case-sensitive collation, which sorts
 * `#elements/CodeMirror` before `#elements/ak-dual-select`.
 */
export const authentikSortImportsConfig: SortImportsConfig = {
    groups,
    customGroups,
    newlinesBetween: true,
    sortSideEffects: true,
    ignoreCase: false,
};
