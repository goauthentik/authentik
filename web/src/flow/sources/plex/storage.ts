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

export function readAttempt(): number {
    return parseInt(readItem(ATTEMPT_KEY) ?? "", 10) || 0;
}

export function writeAttempt(attempt: number): void {
    writeItem(ATTEMPT_KEY, attempt.toString());
}

export function clearAttempts(): void {
    removeItem(ATTEMPT_KEY);
}
