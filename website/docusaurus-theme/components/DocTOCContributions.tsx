import styles from "./DocTOC.module.css";

import Link from "@docusaurus/Link";
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { useLocation } from "@docusaurus/router";
import Translate, { translate } from "@docusaurus/Translate";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import useIsBrowser from "@docusaurus/useIsBrowser";
import React, { type ReactNode } from "react";

export default function DocTOCContributions(): ReactNode {
    const { metadata } = useDoc();
    const { pathname, hash } = useLocation();
    const { siteConfig } = useDocusaurusContext();
    const isBrowser = useIsBrowser();

    // Keep preview/release hosts, but don't share unrelated query parameters.
    const pageUrl = new URL(pathname, isBrowser ? window.location.origin : siteConfig.url);
    pageUrl.hash = hash;

    const issueUrl = new URL("https://github.com/goauthentik/authentik/issues/new");
    issueUrl.search = new URLSearchParams({
        template: "2-docs-issue.yml",
        title: `Documentation issue: ${metadata.title}`,
        link: pageUrl.toString(),
    }).toString();

    return (
        <section className={styles.contributions} aria-label="Help improve this page">
            <h2 className={styles.heading}>
                <Translate id="docs.toc.contributions.heading">Help improve this page</Translate>
            </h2>
            <ul className={styles.contributionLinks}>
                <li>
                    <a
                        href={issueUrl.toString()}
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label={translate({
                            id: "docs.toc.reportIssue.ariaLabel",
                            message: "Report an issue (opens in a new tab)",
                        })}
                    >
                        <svg
                            className={styles.contributionIcon}
                            aria-hidden="true"
                            focusable="false"
                            viewBox="0 0 16 16"
                        >
                            <circle cx="8" cy="8" r="6" />
                            <path d="M8 4.5v4" />
                            <circle cx="8" cy="11" r="0.75" fill="currentColor" stroke="none" />
                        </svg>
                        <Translate id="docs.toc.reportIssue">Report an issue</Translate>
                        <span className={styles.externalIcon} aria-hidden="true">
                            ↗
                        </span>
                    </a>
                </li>
                {metadata.editUrl ? (
                    <li>
                        <a
                            href={metadata.editUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label={translate({
                                id: "docs.toc.edit.ariaLabel",
                                message: "Edit on GitHub (opens in a new tab)",
                            })}
                        >
                            <svg
                                className={styles.contributionIcon}
                                aria-hidden="true"
                                focusable="false"
                                viewBox="0 0 16 16"
                            >
                                <path d="m10.5 2.5 3 3-8 8-4 1 1-4zM8.5 4.5l3 3" />
                            </svg>
                            <Translate id="docs.toc.edit">Edit on GitHub</Translate>
                            <span className={styles.externalIcon} aria-hidden="true">
                                ↗
                            </span>
                        </a>
                    </li>
                ) : null}
                <li>
                    <Link
                        to="https://docs.goauthentik.io/developer-docs/contributing/"
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label={translate({
                            id: "docs.toc.contributorGuide.ariaLabel",
                            message: "Contributor Guide (opens in a new tab)",
                        })}
                    >
                        <svg
                            className={styles.contributionIcon}
                            aria-hidden="true"
                            focusable="false"
                            viewBox="0 0 16 16"
                        >
                            <path d="M8 3.5C6 2 3.5 2 1.5 2.5v10C3.5 12 6 12 8 13.5c2-1.5 4.5-1.5 6.5-1v-10C12.5 2 10 2 8 3.5Zm0 0v10" />
                        </svg>
                        <Translate id="docs.toc.contributorGuide">Contributor Guide</Translate>
                        <span className={styles.externalIcon} aria-hidden="true">
                            ↗
                        </span>
                    </Link>
                </li>
            </ul>
        </section>
    );
}
