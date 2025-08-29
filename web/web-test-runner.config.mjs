/**
 * @file Web Test Runner configuration.
 * @see https://modern-web.dev/docs/test-runner/cli-and-configuration/
 */

/**
 * @type {import('@web/test-runner').TestRunnerConfig}
 */
const config = {
    files: ["dist/**/*.spec.js"],
    nodeResolve: {
        exportConditions: ["browser", "production"],
    },
};

export default config;
