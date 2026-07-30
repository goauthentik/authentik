/**
 * @file User agent utilities.
 */

/**
 * Predicate to determine if the current browser is Safari.
 */
export function isSafari(): boolean {
    const ua = navigator.userAgent.toLowerCase();
    return ua.includes("safari") && !ua.includes("chrome") && !ua.includes("chromium");
}

/**
 * Predicate to determine if the current browser is Firefox.
 */
export function isFirefox(): boolean {
    const ua = navigator.userAgent.toLowerCase();
    return ua.includes("firefox");
}
