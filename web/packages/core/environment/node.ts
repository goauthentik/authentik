/**
 * @file Utility functions for working with environment variables.
 */
/// <reference types="../types/node.js" />

//#region Constants

/**
 * The current Node.js environment, defaulting to "development" when not set.
 *
 * Note, this should only be used during the build process.
 *
 * If you need to check the environment at runtime, use `process.env.NODE_ENV` to
 * ensure that module tree-shaking works correctly.
 *
 * @category Environment
 * @runtime node
 */
export const NodeEnvironment = process.env.NODE_ENV || "development";

/**
 * A source environment variable, which can be a string, number, boolean, null, or undefined.
 */
export type EnvironmentVariable = string | number | boolean | null | undefined;

/**
 * A type helper for serializing environment variables.
 *
 * @category Environment
 */
export type JSONify<T extends EnvironmentVariable> = T extends string ? `"${T}"` : T;

/**
 * A mapping of environment variable names to their source values.
 */
export type EnvRecord = Record<string, EnvironmentVariable>;

/**
 * The result of serializing an {@linkcode EnvRecord}, i.e. each key prefixed and
 * each value replaced with its JSON representation.
 */
export type SerializedEnvRecord<R extends EnvRecord, Prefix extends string> = {
    [K in keyof R & string as `${Prefix}${K}`]: JSONify<R[K]>;
};

//#endregion

//#region Utilities

/**
 * Given an object of environment variables, serializes them into a mapping of
 * environment variable names to their respective runtime constants.
 *
 * This is useful for defining environment variables while bundling with ESBuild, Vite, etc.
 *
 * @category Environment
 * @runtime node
 */
export function serializeEnvironmentVars<
    R extends EnvRecord,
    Prefix extends string = "import.meta.env.",
>(input: R, prefix: Prefix = "import.meta.env." as Prefix): SerializedEnvRecord<R, Prefix> {
    const env = Object.fromEntries(
        Object.entries(input).map(([key, value]) => [prefix + key, JSON.stringify(value ?? "")]),
    );

    return env as SerializedEnvRecord<R, Prefix>;
}

//#endregion
