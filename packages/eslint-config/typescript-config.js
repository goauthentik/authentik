// @ts-check
import tseslint from "typescript-eslint";

/**
 * ESLint configuration for TypeScript authentik projects.
 */
export const typescriptConfig = tseslint.config({
    rules: {
        "@typescript-eslint/ban-ts-comment": [
            "warn",
            {
                "ts-ignore": "allow-with-description",
            },
        ],
        "@typescript-eslint/ban-types": "off",
        "@typescript-eslint/no-empty-interface": "off",
        "@typescript-eslint/no-explicit-any": "off",
        "@typescript-eslint/no-extra-semi": "off",
        "@typescript-eslint/no-misused-new": "off",
        "@typescript-eslint/no-non-null-assertion": "off",
        "@typescript-eslint/no-shadow": [
            "warn",
            {
                ignoreFunctionTypeParameterNameValueShadow: true,
                ignoreTypeValueShadow: true,
            },
        ],
        "@typescript-eslint/no-unused-vars": [
            "warn",
            {
                args: "all",
                argsIgnorePattern: "^_",
                caughtErrors: "all",
                caughtErrorsIgnorePattern: "^_",
                destructuredArrayIgnorePattern: "^_",
                // Ignore all variables, since Prettier takes care of this.
                varsIgnorePattern: "^\\w",
                ignoreRestSiblings: true,
            },
        ],
        "@typescript-eslint/no-var-requires": "off",

        "eqeqeq": ["error", "always", { null: "ignore" }],
        "no-shadow": "off",
        "no-extra-semi": "off",
        "no-undef": "off",
        "no-unused-vars": "off",
        "object-shorthand": [
            "warn",
            "always",
            {
                avoidQuotes: true,
                ignoreConstructors: true,
                avoidExplicitReturnArrows: false,
            },
        ],
        "prefer-const": "warn",
    },
});

export default typescriptConfig;
