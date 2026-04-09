/**
 * @file ESLint Configuration
 *
 * @import { Config } from "eslint/config";
 */

import { createESLintPackageConfig } from "@goauthentik/eslint-config";

/**
 * @type {Config[]}
 */
const eslintConfig = createESLintPackageConfig({
    parserOptions: {
        tsconfigRootDir: import.meta.dirname,
    },
});

export default eslintConfig;
