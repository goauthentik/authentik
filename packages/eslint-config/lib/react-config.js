import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import { defineConfig } from "eslint/config";

// @ts-check

const files = ["**/*.{js,jsx,mjs,cjs,ts,tsx}"];

/**
 * ESLint configuration for React authentik projects.
 */
export const reactConfig = defineConfig(
    {
        files,
        extends: [
            // @ts-expect-error 2322 - Type definition isn't specific enough to omit undefined.
            react.configs.flat.recommended,
        ],
        rules: {
            "react/jsx-uses-react": 0,
            "react/display-name": "off",
            "react/jsx-curly-brace-presence": "error",
            "react/jsx-no-leaked-render": "error",
            "react/prop-types": "off",
            "react/react-in-jsx-scope": "off",
        },
        settings: {
            react: {
                version: "detect",
            },
        },
    },
    {
        files,
        extends: [reactHooks.configs.flat.recommended],
        rules: {
            "react-hooks/rules-of-hooks": "error",
            "react-hooks/exhaustive-deps": "warn",
        },
    },
);

export default reactConfig;
