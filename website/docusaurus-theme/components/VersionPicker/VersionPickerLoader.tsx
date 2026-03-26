import { useHostname } from "#components/VersionPicker/utils.ts";
import { VersionDropdown } from "#components/VersionPicker/VersionDropdown.tsx";

import type {
    AKReleaseFrontMatter,
    AKReleasesPluginData,
} from "@goauthentik/docusaurus-theme/releases/common";

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
    const { preReleaseOrigin } = pluginData.env;

    const [releases, setReleases] = useState(() =>
        pluginData.releases.map((release) => release.name),
    );

    const frontMatterRecord = useMemo(() => {
        const record: Record<string, AKReleaseFrontMatter> = {};

        for (const release of pluginData.releases) {
            if (!release.frontMatter) {
                continue;
            }

            record[release.name] = release.frontMatter;
        }

        return record;
    }, [pluginData.releases]);

    const browser = useIsBrowser();
    const hostname = useHostname();

    useEffect(() => {
        if (!browser || !preReleaseOrigin) return;

        const controller = new AbortController();
        const updateURL = new URL(pluginData.publicPath, preReleaseOrigin);

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
    }, [browser, pluginData.publicPath, preReleaseOrigin]);

    return (
        <VersionDropdown
            hostname={hostname}
            releases={releases}
            frontMatterRecord={frontMatterRecord}
            environment={pluginData.env}
        />
    );
};
