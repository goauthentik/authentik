/**
 * @file Shared utilities for the live reload plugin.
 *
 * @import { BaseLogger } from "@goauthentik/logger-js";
 */

/**
 * Creates a logger with the given prefix.
 *
 * @param {string} [prefix]
 * @returns {BaseLogger}
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
