/**
 * @file Logger utility functions
 */

/**
 * Create a logger function for a mixin.
 *
 * @param prefix The prefix to use for the logger.
 * @param className The class name of the mixin.
 * @returns A logger function.
 */
export function createDebugLogger(
    prefix: string,
    instance?: string | object,
): (...args: unknown[]) => void {
    const namespace = typeof instance === "string" ? instance : instance?.constructor.name;
    const prefixedNamespace = namespace ? `${prefix}/${namespace}` : prefix;

    return console.debug.bind(console, `%c[${prefixedNamespace}]:%c`, "font-weight: bold;", "");
}
