import type { AKReleasesPluginData } from "@goauthentik/docusaurus-theme/releases/plugin";

import { usePluginData } from "@docusaurus/useGlobalData";
import useIsBrowser from "@docusaurus/useIsBrowser";
import { useMemo } from "react";
import { coerce } from "semver";

export const LocalhostAliases: ReadonlySet<string> = new Set(["localhost", "127.0.0.1"]);

/**
 * Given a semver, create the URL for the version.
 */
export function createVersionURL(semver: string): string {
    const subdomain = `version-${semver.replace(".", "-")}`;

    return `https://${subdomain}.goauthentik.io`;
}

/**
 * Given a hostname, parse the semver from the subdomain.
 */
export function parseBranchSemVer(hostname?: string | null): string | null {
    if (!hostname) return null;

    const [, possibleSemVer] = hostname.match(/version-(.+)/) || [];

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

export function useCachedVersionPluginData(): AKReleasesPluginData | null {
    const pluginData = usePluginData("ak-releases-plugin", undefined) as
        | AKReleasesPluginData
        | undefined;

    return pluginData ?? null;
}

function preferredPreReleaseOrigin(browser: boolean, fallback: string): string {
    if (browser && LocalhostAliases.has(window.location.hostname)) {
        return window.location.origin;
    }

    return fallback;
}

export function useVersionPluginData(): AKReleasesPluginData | null {
    const browser = useIsBrowser();
    const cachedPluginData = useCachedVersionPluginData();

    return useMemo(() => {
        if (!cachedPluginData) return null;

        const preReleaseOrigin = preferredPreReleaseOrigin(
            browser,
            cachedPluginData.env.preReleaseOrigin,
        );

        return {
            ...cachedPluginData,
            env: {
                ...cachedPluginData.env,
                preReleaseOrigin,
            },
        };
    }, [browser, cachedPluginData]);
}
