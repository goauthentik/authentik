import "./styles.css";

import {
    createVersionURL,
    normalizeReleaseName,
    parseBranchSemVer,
} from "#components/VersionPicker/utils.ts";

import type {
    AKReleaseFrontMatter,
    AKReleasesPluginEnvironment,
} from "@goauthentik/docusaurus-theme/releases/common";

import clsx from "clsx";
import React, { memo } from "react";

export interface VersionDropdownProps {
    /**
     * The hostname of the client.
     */
    hostname: string | null;

    environment: AKReleasesPluginEnvironment;

    /**
     * The available versions of the documentation.
     *
     * @format semver
     */
    releases: string[];

    /**
     * A possible record of parsed front-matter for each release.
     */
    frontMatterRecord: Record<string, AKReleaseFrontMatter>;
}

/**
 * A dropdown that shows the available versions of the documentation.
 */
export const VersionDropdown = memo<VersionDropdownProps>((props) => {
    const { environment, releases, frontMatterRecord } = props;

    const { branch, preReleaseOrigin } = environment;
    const parsedSemVer = parseBranchSemVer(branch);

    const currentLabel = parsedSemVer || "Pre-release";

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
                {branch ? (
                    <>
                        <li>
                            <a
                                href={preReleaseOrigin}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="dropdown__link menu__link"
                            >
                                ✨ Pre-release
                            </a>
                        </li>
                        <hr className="separator" />
                    </>
                ) : null}

                {visibleReleases.map((releaseName, idx) => {
                    const semVer = normalizeReleaseName(releaseName);

                    let label = releaseName;
                    const frontmatter = frontMatterRecord[semVer];

                    if (frontmatter?.draft) {
                        return null;
                    }

                    if (idx === 0 && !frontmatter?.beta && semVer === releaseName) {
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
