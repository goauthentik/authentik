import { type KnipConfig } from "knip";

const config: KnipConfig = {
    entry: [
        "./src/admin/index.entrypoint.ts",
        "./src/user/index.entrypoint.ts",
        "./src/flow/index.entrypoint.ts",
        "./src/standalone/api-browser/index.entrypoint.ts",
        "./src/rac/index.entrypoint.ts",
        "./src/standalone/loading/index.entrypoint.ts",
        "./src/polyfill/index.entrypoint.ts",
    ],
    ignore: ["packages/client-ts/**", "out/**/*"],

    project: ["src/**/*.ts", "src/**/*.js", "./scripts/*.mjs", ".storybook/*.ts"],
    // "ignore": ["src/**/*.test.ts", "src/**/*.stories.ts"],
    // Prevent Knip from complaining about web components, which export their classes but also
    // export their registration, and we don't always use both.
    ignoreExportsUsedInFile: true,
    typescript: {
        config: ["tsconfig.json"],
    },
    wireit: {
        config: ["package.json"],
    },
    storybook: {
        config: [".storybook/{main,test-runner}.{js,ts}"],
        entry: [
            ".storybook/{manager,preview}.{js,jsx,ts,tsx}",
            "**/*.@(mdx|stories.@(mdx|js|jsx|mjs|ts|tsx))",
        ],
        project: [".storybook/**/*.{js,jsx,ts,tsx}"],
    },
    eslint: {
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
};

export default config;
