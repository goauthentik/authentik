/**
 * @file Constants for JavaScript and TypeScript files.
 *
 */

/**
 * The current Node.js environment, defaulting to "development" when not set.
 *
 * Note, this should only be used during the build process.
 *
 * If you need to check the environment at runtime, use `process.env.NODE_ENV` to
 * ensure that module tree-shaking works correctly.
 *
 */
export const NodeEnvironment = /** @type {'development' | 'production'} */ (
    process.env.NODE_ENV || "development"
);
