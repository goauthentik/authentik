/**
 * @file Stylelint configuration for the web UI. Extends `stylelint-config-recommended` rather than
 *   `-standard`: recommended is the correctness-only set, while standard layers on stylistic
 *   conventions oxfmt already decides. The two disagree — `rule-empty-line-before` alone wants 1394
 *   edits oxfmt does not make. Same division of labor as oxlint and oxfmt: stylelint judges what
 *   the CSS means, oxfmt decides how it is laid out. Rules switched off below are pre-existing
 *   debt, each with the count it currently reports. They are off so the check can gate on
 *   everything else; turning one back on is a self-contained cleanup.
 * @type {import("stylelint").Config}
 */

import { fileURLToPath } from "node:url";

/**
 * Stylelint resolves `extends` from its own location in the store rather than from this file, which
 * the isolated linker turns into "Could not find stylelint-config-recommended". Resolving it here
 * pins it to this package's own dependency.
 *
 * `import.meta.resolve` rather than `require.resolve`: the preset ships an import-only `exports`
 * map, so the CJS resolver cannot see it at all.
 */
const recommended = fileURLToPath(import.meta.resolve("stylelint-config-recommended"));
export default {
    extends: [recommended],
    ignoreFiles: [
        // Third-party CSS we do not author.
        "**/vendor/**",
        "**/vendored/**",
        "**/*.min.css",
        // Build output.
        "dist/**",
        "storybook-static/**",
        "**/node_modules/**",
    ],
    rules: {
        "custom-property-pattern": null, // 3 — house kebab-case convention, never enforced before.
        "selector-class-pattern": null, // 16 — same, and renaming a class means touching templates.
        "no-duplicate-selectors": null, // 92 — refactor-scale.
        "no-descending-specificity": null, // 32 — refactor-scale, and noisy by reputation.
        "declaration-block-no-duplicate-properties": null, // 6
        "declaration-block-no-duplicate-custom-properties": null, // 6
        "declaration-block-no-shorthand-property-overrides": null, // 2
        "font-family-no-missing-generic-family-keyword": null, // 3
        "declaration-property-value-keyword-no-deprecated": null, // 3
        // `display: box` is the legacy flexbox line-clamp fallback, paired with `-webkit-box`.
        // Deliberate, so this one stays off rather than being burned down.
        "declaration-property-value-no-unknown": null,
        // `text-stroke-{width,color}` are the unprefixed companions to `-webkit-text-stroke-*`,
        // written for the day the prefix drops. Scoped rather than switched off wholesale.
        "property-no-unknown": [
            true,
            { ignoreProperties: ["text-stroke-width", "text-stroke-color"] },
        ],
    },
};
