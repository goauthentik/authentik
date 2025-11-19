/**
 * @file Shared utilities for the live reload plugin.
 *
 * @import { BaseLogger } from "pino";
 */

/**
 * @typedef {Pick<BaseLogger, "info" | "warn" | "error" | "debug">} Logger
 */

/**
 * Creates a logger with the given prefix.
 *
 * @param {string} [prefix]
 * @returns {Logger}
 */
export function createLogger(prefix = "[Build Observer]") {
    return {
        info: console.log.bind(console, prefix),
        warn: console.warn.bind(console, prefix),
        error: console.error.bind(console, prefix),
        debug: console.debug.bind(console, prefix),
    };
}
