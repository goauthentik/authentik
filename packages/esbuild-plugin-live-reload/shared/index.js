/**
 * @file Shared utilities for the live reload plugin.
 */

/**
 * The subset of the console API this plugin logs through.
 *
 * Declared here rather than borrowed from a logging package so that neither the
 * plugin nor its published types require one: any `console` will do.
 *
 * @typedef {object} ConsoleLike
 * @property {typeof console.info} info
 * @property {typeof console.warn} warn
 * @property {typeof console.error} error
 * @property {typeof console.debug} debug
 * @property {typeof console.trace} trace
 */

/**
 * Creates a logger with the given prefix.
 *
 * @param {string} [prefix]
 * @returns {ConsoleLike}
 */
export function createLogger(prefix = "[Build Observer]") {
    return {
        info: console.log.bind(console, prefix),
        warn: console.warn.bind(console, prefix),
        error: console.error.bind(console, prefix),
        debug: console.debug.bind(console, prefix),
        trace: console.trace.bind(console, prefix),
    };
}
