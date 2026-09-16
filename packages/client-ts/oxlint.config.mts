/**
 * @file Oxlint configuration for the generated API client.
 *
 * This exists for exactly one rule. The generator emits `import { mapValues } from "../runtime"`
 * into every model whether it is used or not, and the Prettier import plugin this repo used to run
 * stripped the unused ones on its way past (`keepUnused: []`). Nothing replaces that now, so the
 * generation pipeline asks oxlint to do it.
 *
 * Nothing else is switched on. This is generated code, and `make gen-clients` is not the place to
 * discover lint opinions about it.
 */

export default {
    plugins: ["typescript"],
    categories: {},
    rules: {
        "no-unused-vars": ["warn", { args: "none", varsIgnorePattern: "^_" }],
    },
    ignorePatterns: ["**/node_modules", "**/dist", "**/out", "docs/**"],
};
