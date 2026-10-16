/**
 * @file Oxlint configuration.
 */

import { createOxlintConfig } from "@goauthentik/oxlint-config";

const config = createOxlintConfig({
    overrides: {
        rules: {
            "no-unused-vars": ["warn", { fix: { imports: "safe-fix" }, args: "none" }],
            // The generated code often includes `== true` checks which we can't fix automatically.
            "eqeqeq": "off",
        },
    },
});

export default config;
