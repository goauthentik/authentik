/**
 * @file Constants for JavaScript and TypeScript files.
 */

/// <reference types="../../types/global.js" />

/**
 * The current Node.js environment, defaulting to "development" when not set.
 *
 * Note, this should only be used during the build process.
 *
 * If you need to check the environment at runtime, use `process.env.NODE_ENV` to
 * ensure that module tree-shaking works correctly.
 *
 */
export const NodeEnvironment = process.env.NODE_ENV || "development";
