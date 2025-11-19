import { RedirectEntry } from "@goauthentik/docusaurus-theme/redirects";
import type { AKRedirectsPluginData } from "@goauthentik/docusaurus-theme/redirects/plugin";

import { usePluginData } from "@docusaurus/useGlobalData";

/**
 * Hook to retrieve redirects provided by the client-side redirects plugin.
 */
export function useRedirectEntries(): RedirectEntry[] | null {
    const pluginData = usePluginData("ak-redirects-plugin", undefined) as
        | AKRedirectsPluginData
        | undefined;

    if (!pluginData || !pluginData.redirects) {
        return null;
    }

    return pluginData.redirects;
}

/**
 * Given a URL-like object, return the pathname (i.e. suffix), and the combination query string, hash, etc (i.e. prefix).
 */
export function pluckPathnameAffixes(
    url: Pick<URL, "pathname" | "href" | "origin">,
): [prefix: string, suffix: string] {
    const [, fullPathname = ""] = url.href.split(window.location.origin);

    if (!fullPathname) return ["", ""];

    const suffix = fullPathname.slice(url.pathname.length);

    return [url.pathname, suffix];
}
