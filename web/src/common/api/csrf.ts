import { parseCookie } from "cookie";

/**
 * Header the server expects the CSRF token in.
 */
export const CSRFHeaderName = "X-authentik-CSRF";

/**
 * Name of the cookie holding the CSRF token.
 */
const CSRFCookieName = "authentik_csrf";

/**
 * @returns The CSRF token from the cookies, or an empty string if not present.
 */
export function readCSRFToken(): string {
    return parseCookie(document.cookie)[CSRFCookieName] ?? "";
}
