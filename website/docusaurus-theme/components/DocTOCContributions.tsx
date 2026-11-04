import styles from "./DocTOC.module.css";

import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { useLocation } from "@docusaurus/router";
import Translate, { translate } from "@docusaurus/Translate";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import useIsBrowser from "@docusaurus/useIsBrowser";
import React, { type ReactNode, useId } from "react";

interface ContributionLinkProps {
    href: string;
    /** Accessible name; the visible label plus "(opens in a new tab)". */
    ariaLabel: string;
    /** Shapes drawn in a 16×16 outline icon. */
    icon: ReactNode;
    children: ReactNode;
}

function ContributionLink({ href, ariaLabel, icon, children }: ContributionLinkProps): ReactNode {
    return (
        <li>
            <a href={href} target="_blank" rel="noopener noreferrer" aria-label={ariaLabel}>
                <svg
                    className={styles.contributionIcon}
                    aria-hidden="true"
                    focusable="false"
                    viewBox="0 0 16 16"
                >
                    {icon}
                </svg>
                {children}
                <span className={styles.externalIcon} aria-hidden="true">
                    ↗
                </span>
            </a>
        </li>
    );
}

export default function DocTOCContributions(): ReactNode {
    const { metadata } = useDoc();
    const { pathname, hash } = useLocation();
    const { siteConfig } = useDocusaurusContext();
    const isBrowser = useIsBrowser();
    const headingID = useId();

    // Keep preview and release hosts, but don't share unrelated query parameters.
    // The server render knows neither the host nor the hash, so both wait for
    // hydration to keep the first client render identical to the HTML.
    const pageUrl = new URL(pathname, isBrowser ? window.location.origin : siteConfig.url);
    if (isBrowser) {
        pageUrl.hash = hash;
    }

    const issueUrl = new URL("https://github.com/goauthentik/authentik/issues/new");
    issueUrl.search = new URLSearchParams({
        template: "2-docs-issue.yml",
        title: `Documentation issue: ${metadata.title}`,
        link: pageUrl.toString(),
    }).toString();

    return (
        <section className={styles.contributions} aria-labelledby={headingID}>
            <h2 id={headingID} className={styles.heading}>
                <Translate id="docs.toc.contributions.heading">Help improve this page</Translate>
            </h2>
            <ul className={styles.contributionLinks}>
                <ContributionLink
                    href={issueUrl.toString()}
                    ariaLabel={translate({
                        id: "docs.toc.reportIssue.ariaLabel",
                        message: "Report an issue (opens in a new tab)",
                    })}
                    icon={
                        <>
                            <circle cx="8" cy="8" r="6" />
                            <path d="M8 4.5v4" />
                            <circle cx="8" cy="11" r="0.75" fill="currentColor" stroke="none" />
                        </>
                    }
                >
                    <Translate id="docs.toc.reportIssue">Report an issue</Translate>
                </ContributionLink>
                {metadata.editUrl ? (
                    <ContributionLink
                        href={metadata.editUrl}
                        ariaLabel={translate({
                            id: "docs.toc.edit.ariaLabel",
                            message: "Edit on GitHub (opens in a new tab)",
                        })}
                        icon={<path d="m10.5 2.5 3 3-8 8-4 1 1-4zM8.5 4.5l3 3" />}
                    >
                        <Translate id="docs.toc.edit">Edit on GitHub</Translate>
                    </ContributionLink>
                ) : null}
                <ContributionLink
                    href="https://docs.goauthentik.io/developer-docs/contributing/"
                    ariaLabel={translate({
                        id: "docs.toc.contributorGuide.ariaLabel",
                        message: "Contributor Guide (opens in a new tab)",
                    })}
                    icon={
                        <path d="M8 3.5C6 2 3.5 2 1.5 2.5v10C3.5 12 6 12 8 13.5c2-1.5 4.5-1.5 6.5-1v-10C12.5 2 10 2 8 3.5Zm0 0v10" />
                    }
                >
                    <Translate id="docs.toc.contributorGuide">Contributor Guide</Translate>
                </ContributionLink>
                <ContributionLink
                    href="https://goauthentik.io/pricing/"
                    ariaLabel={translate({
                        id: "docs.toc.enterpriseSupport.ariaLabel",
                        message: "Get Enterprise Support (opens in a new tab)",
                    })}
                    icon={
                        <>
                            <circle cx="8" cy="8" r="6" />
                            <circle cx="8" cy="8" r="2.5" />
                            <path d="m3.75 3.75 2.5 2.5m3.5 3.5 2.5 2.5m0-8.5-2.5 2.5m-3.5 3.5-2.5 2.5" />
                        </>
                    }
                >
                    <Translate id="docs.toc.enterpriseSupport">Get Enterprise Support</Translate>
                </ContributionLink>
            </ul>
        </section>
    );
}
