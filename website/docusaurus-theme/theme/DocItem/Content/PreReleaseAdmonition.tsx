import Link from "@docusaurus/Link";
import { ThemeClassNames } from "@docusaurus/theme-common";
import Translate from "@docusaurus/Translate";
import Admonition from "@theme/Admonition";
import type { Props } from "@theme/ContentVisibility/Unlisted";
import ExternalLinkIcon from "@theme/Icon/ExternalLink";
import clsx from "clsx";
import React from "react";

export const PreReleaseAdmonition: React.FC<Props> = ({ className }) => {
    return (
        <Admonition
            type="info"
            title={
                <Translate
                    id="theme.contentVisibility.unlistedBanner.preRelease.title"
                    description="The unlisted content banner title"
                >
                    Pre-Release Documentation
                </Translate>
            }
            className={clsx(className, ThemeClassNames.common.unlistedBanner)}
        >
            <p>
                <Translate
                    id="theme.contentVisibility.unlistedBanner.preRelease.message"
                    description="The unlisted content banner message"
                    values={{
                        releasesLink: (
                            <Link
                                to="https://github.com/goauthentik/authentik/releases"
                                target="_blank"
                            >
                                <Translate
                                    id="theme.contentVisibility.unlistedBanner.githubReleasesLinkLabel"
                                    description="The link label to the GitHub releases page"
                                >
                                    GitHub releases
                                </Translate>
                                <ExternalLinkIcon />
                            </Link>
                        ),
                    }}
                >
                    {`We’re publishing these release notes as a preview of what's to come. To try a release candidate, find the latest RC version on {releasesLink}, then update your Docker image tag accordingly.`}
                </Translate>
            </p>

            <p>
                <Link to="/install-config/beta/">
                    <Translate
                        id="theme.contentVisibility.unlistedBanner.preRelease.betaTestingLinkLabel"
                        description="The link label to the beta testing documentation"
                    >
                        Read more about beta testing
                    </Translate>
                </Link>
            </p>
        </Admonition>
    );
};
