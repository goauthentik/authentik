import { LocalhostAliases, ProductionURL, useHostname } from "#components/VersionPicker/utils.ts";
import { VersionDropdown } from "#components/VersionPicker/VersionDropdown.tsx";

import { AKReleasesPluginData } from "@goauthentik/docusaurus-theme/releases/plugin";

import useIsBrowser from "@docusaurus/useIsBrowser";
import React, { useEffect, useMemo, useState } from "react";

export interface VersionPickerLoaderProps {
    pluginData: AKReleasesPluginData;
}

/**
 * A data-fetching component that loads available versions of the documentation.
 *
 * @see {@linkcode VersionPicker} for the component.
 * @see {@linkcode AKReleasesPluginData} for the plugin data.
 * @client
 */
export const VersionPickerLoader: React.FC<VersionPickerLoaderProps> = ({ pluginData }) => {
    const [releases, setReleases] = useState(pluginData.releases);

    const browser = useIsBrowser();
    const hostname = useHostname();

    const prereleaseOrigin = useMemo(() => {
        if (browser && LocalhostAliases.has(window.location.hostname)) {
            return window.location.origin;
        }

        return ProductionURL.href;
    }, [browser]);

    useEffect(() => {
        if (!browser || !prereleaseOrigin) return;

        const controller = new AbortController();
        const updateURL = new URL(pluginData.publicPath, prereleaseOrigin);

        fetch(updateURL, {
            signal: controller.signal,
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Failed to fetch new releases: ${response.status}`);
                }

                return response.json();
            })
            .then((data: unknown) => {
                // We're extra cautious here to be ready if the API shape ever changes.
                if (!data) throw new Error("Failed to parse releases");

                if (!Array.isArray(data)) throw new Error("Releases must be an array");

                if (!data.every((item) => typeof item === "string"))
                    throw new Error("Releases must be an array of strings");

                setReleases(data);
            })
            .catch((error) => {
                console.warn(`Failed to fetch new releases: ${error}`);
            });

        // eslint-disable-next-line consistent-return
        return () => controller.abort("unmount");
    }, [browser, pluginData.publicPath, prereleaseOrigin]);

    return (
        <VersionDropdown
            hostname={hostname}
            prereleaseOrigin={prereleaseOrigin}
            releases={releases}
        />
    );
};
