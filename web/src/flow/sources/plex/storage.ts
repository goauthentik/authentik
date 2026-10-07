/**
 * @file State for the round trip to app.plex.tv.
 *   The state lives in sessionStorage rather than in the flow URL used as Plex's
 *   forwardUrl. Storage binds the pin to the browser session that started the
 *   round trip: a pin id carried in the URL could be forged, letting an attacker
 *   authorize a pin with their own Plex account and hand the resulting link to a
 *   victim (login CSRF).
 */

const PENDING_KEY = "authentik-plex-pin";
const ATTEMPT_KEY = "authentik-plex-attempt";

/**
 * Query parameter added to the forwardUrl handed to Plex. A pending sign-in
 * only counts as a return when the page was loaded with it: a pin left behind
 * by a round trip the user walked away from (the Back button, an expired Plex
 * page, a typed URL) is stale, and must not turn the next fresh sign-in into
 * "cancelled or timed out".
 */
export const RETURN_PARAM = "plex_return";

/**
 * A sign-in that left for app.plex.tv and has not come back yet.
 */
export interface PendingPlexSignIn {
    /**
     * The slug of the source the sign-in started from. Plex returns the
     * browser to the flow, not to the source, so this is what picks which
     * source's stage picks the sign-in back up.
     */
    slug: string;
    /** The pin Plex was asked to authorize. */
    pin: number;
}

// sessionStorage access can throw outright in some embedded and lockdown
// contexts; treat that the same as the value being absent.
function readItem(key: string): string | null {
    try {
        return window.sessionStorage.getItem(key);
    } catch {
        return null;
    }
}

function writeItem(key: string, value: string): boolean {
    try {
        window.sessionStorage.setItem(key, value);

        return true;
    } catch {
        return false;
    }
}

function removeItem(key: string): void {
    try {
        window.sessionStorage.removeItem(key);
    } catch {
        // Nothing to clean up if storage is unavailable.
    }
}

export function readPendingSignIn(): PendingPlexSignIn | null {
    const raw = readItem(PENDING_KEY);

    if (!raw) return null;

    try {
        const { slug, pin } = JSON.parse(raw) as Partial<PendingPlexSignIn>;

        if (typeof slug === "string" && slug && Number.isInteger(pin)) {
            return { slug, pin: pin! };
        }
    } catch {
        // Unreadable, e.g. written by an older version; treated as absent.
    }

    return null;
}

/**
 * @returns Whether the sign-in was stored. Without it nothing can recognize
 * the return leg.
 */
export function writePendingSignIn(pending: PendingPlexSignIn): boolean {
    return writeItem(PENDING_KEY, JSON.stringify(pending));
}

export function clearPendingSignIn(): void {
    removeItem(PENDING_KEY);
}

// The query string is handled as raw `name=value` parts rather than through
// URLSearchParams, which would re-encode the other parameters (`next` in
// particular) on the way back out.
function queryParts(search: string): string[] {
    return search.replace(/^\?/, "").split("&").filter(Boolean);
}

function isReturnMarker(part: string): boolean {
    return part.split("=")[0] === RETURN_PARAM;
}

/**
 * @returns The URL Plex should send the browser back to: the current page with
 *   its query string unchanged, plus the return marker.
 */
export function returnUrlFor(location: Pick<Location, "origin" | "pathname" | "search">): string {
    const parts = queryParts(location.search).filter((part) => !isReturnMarker(part));

    parts.push(`${RETURN_PARAM}=1`);

    return `${location.origin}${location.pathname}?${parts.join("&")}`;
}

/**
 * @returns The pending sign-in, but only when this page was loaded as Plex
 *   sending the browser back.
 */
export function readReturningSignIn(): PendingPlexSignIn | null {
    if (!queryParts(window.location.search).some(isReturnMarker)) return null;

    return readPendingSignIn();
}

/**
 * Drop the return marker from the address bar once it has been read, so a
 * reload or a later visit to this history entry does not look like another
 * return.
 */
export function clearReturnMarker(): void {
    const parts = queryParts(window.location.search);

    if (!parts.some(isReturnMarker)) return;

    const rest = parts.filter((part) => !isReturnMarker(part));
    const { pathname, hash } = window.location;
    const search = rest.length ? `?${rest.join("&")}` : "";

    try {
        window.history.replaceState(window.history.state, "", `${pathname}${search}${hash}`);
    } catch {
        // The marker is only a hint; leaving it in place is harmless.
    }
}

export function readAttempt(): number {
    return parseInt(readItem(ATTEMPT_KEY) ?? "", 10) || 0;
}

export function writeAttempt(attempt: number): void {
    writeItem(ATTEMPT_KEY, attempt.toString());
}

export function clearAttempts(): void {
    removeItem(ATTEMPT_KEY);
}
