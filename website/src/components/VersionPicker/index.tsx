import { usePluginData } from "@docusaurus/useGlobalData";
import useIsBrowser from "@docusaurus/useIsBrowser";
import type { AKReleasesPluginData } from "@site/releases/plugin.mjs";
import clsx from "clsx";
import React, { memo, useEffect, useMemo, useState } from "react";
import { coerce } from "semver";

import "./styles.css";

const ProductionURL = new URL("https://docs.goauthentik.io");
const LocalhostAliases: ReadonlySet<string> = new Set(["localhost", "127.0.0.1"]);

/**
 * Given a semver, create the URL for the version.
 */
function createVersionURL(semver: string): string {
    const subdomain = `version-${semver.replace(".", "-")}`;

    return `https://${subdomain}.goauthentik.io`;
}

/**
 * Predicate to determine if a hostname appears to be a prerelease origin.
 */
function isPrerelease(hostname: string | null): boolean {
    if (!hostname) return false;

    if (hostname === ProductionURL.hostname) return true;
    if (hostname.endsWith(".netlify.app")) return true;

    if (LocalhostAliases.has(hostname)) return true;

    return false;
}

/**
 * Given a hostname, parse the semver from the subdomain.
 */
function parseHostnameSemVer(hostname: string | null): string | null {
    if (!hostname) return null;

    const [, possibleSemVer] = hostname.match(/version-(.+)\.goauthentik\.io/) || [];

    if (!possibleSemVer) return null;

    const formattedSemVer = possibleSemVer.replace("-", ".");

    if (!coerce(formattedSemVer)) return null;

    return formattedSemVer;
}

interface VersionDropdownProps {
    /**
     * The hostname of the client.
     */
    hostname: string | null;
    /**
     * The origin of the prerelease documentation.
     *
     * @format url
     */
    prereleaseOrigin: string;
    /**
     * The available versions of the documentation.
     *
     * @format semver
     */
    releases: string[];
}

/**
 * A dropdown that shows the available versions of the documentation.
 */
const VersionDropdown = memo<VersionDropdownProps>(({ hostname, prereleaseOrigin, releases }) => {
    const prerelease = isPrerelease(hostname);
    const parsedSemVer = !prerelease ? parseHostnameSemVer(hostname) : null;

    const currentLabel = parsedSemVer || "Pre-Release";

    const endIndex = parsedSemVer ? releases.indexOf(parsedSemVer) : -1;

    const visibleReleases = releases.slice(0, endIndex === -1 ? 3 : endIndex + 3);

    return (
        <li className="navbar__item dropdown dropdown--hoverable dropdown--right ak-version-selector">
            <div
                aria-haspopup="true"
                aria-expanded="false"
                role="button"
                className="navbar__link menu__link"
            >
                Version: {currentLabel}
            </div>

            <ul className="dropdown__menu menu__list-item--collapsed">
                {!prerelease ? (
                    <li>
                        <a
                            href={prereleaseOrigin}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="dropdown__link menu__link"
                        >
                            Pre-Release
                        </a>
                    </li>
                ) : null}

                {visibleReleases.map((semVer, idx) => {
                    let label = semVer;

                    if (idx === 0) {
                        label += " (Current Release)";
                    }

                    return (
                        <li key={idx}>
                            <a
                                href={createVersionURL(semVer)}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={clsx("dropdown__link menu__link", {
                                    "menu__link--active": semVer === currentLabel,
                                })}
                            >
                                {label}
                            </a>
                        </li>
                    );
                })}
            </ul>
        </li>
    );
});

interface VersionPickerLoaderProps {
    pluginData: AKReleasesPluginData;
}

/**
 * A data-fetching component that loads available versions of the documentation.
 *
 * @see {@linkcode VersionPicker} for the component.
 * @see {@linkcode AKReleasesPluginData} for the plugin data.
 * @client
 */
const VersionPickerLoader: React.FC<VersionPickerLoaderProps> = ({ pluginData }) => {
    const [releases, setReleases] = useState(pluginData.releases);

    const browser = useIsBrowser();

    const prereleaseOrigin = useMemo(() => {
        if (browser && LocalhostAliases.has(window.location.hostname)) {
            return window.location.origin;
        }

        return ProductionURL.href;
    }, [browser]);

    const hostname = useMemo(() => {
        if (!browser) return null;

        const searchParams = new URLSearchParams(window.location.search);

        // Query parameter used for debugging.
        // Note that this doesn't synchronize with Docusaurus's router state.
        const subdomain = searchParams.get("version");

        if (subdomain) return subdomain;

        return window.location.hostname;
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

        return () => controller.abort("unmount");
    }, [browser, prereleaseOrigin]);

    return (
        <VersionDropdown
            hostname={hostname}
            prereleaseOrigin={prereleaseOrigin}
            releases={releases}
        />
    );
};

/**
 * A component that shows the available versions of the documentation.
 *
 * @see {@linkcode VersionPickerLoader} for the data-fetching component.
 */
export const VersionPicker: React.FC = () => {
    const pluginData = usePluginData("ak-releases-plugin", undefined, {
        failfast: true,
    }) as AKReleasesPluginData;

    if (!pluginData.releases.length) return null;

    return <VersionPickerLoader pluginData={pluginData} />;
};
