import { format } from "prettier";
import { AuthentikPrettierConfig } from "./config.js";

/**
 * Format using Prettier.
 *
 * Defaults to using the TypeScript parser.
 *
 * @category Formatting
 * @param {string} fileContents The contents of the file to format.
 *
 * @returns {Promise<string>} The formatted file contents.
 */
export function formatWithPrettier(fileContents) {
    return format(fileContents, {
        ...AuthentikPrettierConfig,
        parser: "typescript",
    });
}
