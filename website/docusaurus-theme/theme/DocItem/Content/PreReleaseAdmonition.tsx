import Link from "@docusaurus/Link";
import { ThemeClassNames } from "@docusaurus/theme-common";
import Translate from "@docusaurus/Translate";
import Admonition from "@theme/Admonition";
import ExternalLinkIcon from "@theme/Icon/ExternalLink";
import React from "react";

export const PreReleaseAdmonition: React.FC = () => {
    return (
        <Admonition
            type="info"
            title={null}
            icon={null}
            className={ThemeClassNames.common.unlistedBanner}
        >
            <p>
                <Translate
                    id="theme.preReleaseAdmonition.message"
                    description="The beta content banner message"
                    values={{
                        releasesLink: (
                            <Link
                                to="https://github.com/goauthentik/authentik/releases"
                                target="_blank"
                            >
                                <Translate
                                    id="theme.githubReleasesLinkLabelAdmonition"
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
                        id="theme.preReleaseAdmonition.betaTestingLinkLabel"
                        description="The link label to the beta testing documentation"
                    >
                        Read more about beta testing
                    </Translate>
                </Link>
            </p>
        </Admonition>
    );
};
