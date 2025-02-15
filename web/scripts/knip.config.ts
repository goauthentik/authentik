import { type KnipConfig } from "knip";

const config: KnipConfig = {
    "entry": [
        "./src/admin/AdminInterface/AdminInterface.ts",
        "./src/user/UserInterface.ts",
        "./src/flow/FlowInterface.ts",
        "./src/standalone/api-browser/index.ts",
        "./src/rac/index.ts",
        "./src/standalone/loading/index.ts",
        "./src/polyfill/poly.ts",
    ],
    "project": ["src/**/*.ts", "src/**/*.js", "./scripts/*.mjs", ".storybook/*.ts"],
    // "ignore": ["src/**/*.test.ts", "src/**/*.stories.ts"],
    // Prevent Knip from complaining about web components, which export their classes but also
    // export their registration, and we don't always use both.
    "ignoreExportsUsedInFile": true,
    "typescript": {
        config: ["tsconfig.json"],
    },
    "wireit": {
        config: ["package.json"],
    },
    "storybook": {
        config: [".storybook/{main,test-runner}.{js,ts}"],
        entry: [
            ".storybook/{manager,preview}.{js,jsx,ts,tsx}",
            "**/*.@(mdx|stories.@(mdx|js|jsx|mjs|ts|tsx))",
        ],
        project: [".storybook/**/*.{js,jsx,ts,tsx}"],
    },
    "eslint": {
        entry: [
            "eslint.config.mjs",
            "scripts/eslint.precommit.mjs",
            "scripts/eslint.nightmare.mjs",
            "scripts/eslint-precommit.mjs",
            "scripts/eslint-nightmare.mjs",
            "scripts/eslint.mjs",
        ],
        config: ["package.json"],
    },
    "webdriver-io": {
        config: ["wdio.conf.js"],
    },
};

export default config;
