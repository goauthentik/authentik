import useIsBrowser from "@docusaurus/useIsBrowser";
import { useMemo } from "react";
import { coerce } from "semver";

export const ProductionURL = new URL("https://docs.goauthentik.io");

export const LocalhostAliases: ReadonlySet<string> = new Set(["localhost", "127.0.0.1"]);

/**
 * Given a semver, create the URL for the version.
 */
export function createVersionURL(semver: string): string {
    const subdomain = `version-${semver.replace(".", "-")}`;

    return `https://${subdomain}.goauthentik.io`;
}

/**
 * Predicate to determine if a hostname appears to be a prerelease origin.
 */
export function isPrerelease(hostname: string | null): boolean {
    if (!hostname) return false;

    if (hostname === ProductionURL.hostname) return true;
    if (hostname.endsWith(".netlify.app")) return true;

    if (LocalhostAliases.has(hostname)) return true;

    return false;
}

/**
 * Given a hostname, parse the semver from the subdomain.
 */
export function parseHostnameSemVer(hostname: string | null): string | null {
    if (!hostname) return null;

    const [, possibleSemVer] = hostname.match(/version-(.+)\.goauthentik\.io/) || [];

    if (!possibleSemVer) return null;

    const formattedSemVer = possibleSemVer.replace("-", ".");

    if (!coerce(formattedSemVer)) return null;

    return formattedSemVer;
}

export function useHostname() {
    const browser = useIsBrowser();

    const hostname = useMemo(() => {
        if (!browser) return null;

        const searchParams = new URLSearchParams(window.location.search);

        // Query parameter used for debugging.
        // Note that this doesn't synchronize with Docusaurus's router state.
        const subdomain = searchParams.get("version");

        if (subdomain) return subdomain;

        return window.location.hostname;
    }, [browser]);

    return hostname;
}

export function usePrereleaseOrigin() {
    const browser = useIsBrowser();

    const prereleaseOrigin = useMemo(() => {
        if (browser && LocalhostAliases.has(window.location.hostname)) {
            return window.location.origin;
        }

        return ProductionURL.href;
    }, [browser]);

    return prereleaseOrigin;
}
