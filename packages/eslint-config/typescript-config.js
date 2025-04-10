// @ts-check
import tseslint from "typescript-eslint";

/**
 * ESLint configuration for TypeScript authentik projects.
 */
export const typescriptConfig = tseslint.config({
    rules: {
        "@typescript-eslint/ban-ts-comment": [
            "error",
            {
                "ts-expect-error": "allow-with-description",
                "ts-ignore": true,
                "ts-nocheck": "allow-with-description",
                "ts-check": false,
                "minimumDescriptionLength": 5,
            },
        ],
        "no-use-before-define": "off",
        "@typescript-eslint/no-use-before-define": "error",
        "no-invalid-this": "off",
        "no-unused-vars": "off",
        "@typescript-eslint/no-namespace": "off",
        "@typescript-eslint/no-unused-vars": [
            "warn",
            {
                argsIgnorePattern: "^_",
                varsIgnorePattern: "^_",
                caughtErrorsIgnorePattern: "^_",
            },
        ],
    },
});

export default typescriptConfig;
