/**
 * @file Oxfmt configuration
 */

const baseConfig = await import("@goauthentik/oxfmt-config-dev")
    .catch(() => {
        console.debug("Fallback to published @goauthentik/oxfmt-config");

        // @ts-expect-error - Remove ignore after package is published.
        return import("@goauthentik/oxfmt-config");
    })
    .then((module) => module.default);

export default {
    ...baseConfig,
    overrides: [
        ...(baseConfig.overrides ?? []),
        {
            // oxfmt 0.56's JSDoc formatter is non-idempotent on these comments — it oscillates and
            // can corrupt fenced `@example` blocks. Skip the JSDoc pass for them until it is fixed
            // upstream; layout and import formatting still apply.
            files: ["src/elements/ak-table/ak-select-table.ts", "src/elements/utils/attributes.ts"],
            options: { jsdoc: false },
        },
    ],
};
