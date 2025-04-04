/**
 * @file HTTP utilities.
 */

/**
 * Get the value of a cookie by its name.
 *
 * @param cookieName - The name of the cookie to retrieve.
 * @returns The value of the cookie, or an empty string if the cookie is not found.
 */
export function getCookie(cookieName: string): string {
    if (!cookieName) return "";
    if (typeof document === "undefined") return "";
    if (typeof document.cookie !== "string") return "";
    if (!document.cookie) return "";

    const search = cookieName + "=";
    // Split the cookie string into individual name=value pairs...
    const keyValPairs = document.cookie.split(";").map((cookie) => cookie.trim());

    for (const pair of keyValPairs) {
        if (!pair.startsWith(search)) continue;

        return decodeURIComponent(pair.substring(search.length));
    }

    return "";
}
