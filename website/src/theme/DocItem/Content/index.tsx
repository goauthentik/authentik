/// <reference types="@docusaurus/plugin-content-docs" />
/**
 * @file Swizzled DocItemContent component.
 *
 * This component is a swizzled version of the original DocItemContent component.
 *
 * Similar to Docusaurus' default `DocItemContent`, this component renders
 * the content of a documentation page. However, it also adds support for
 * support badges, and Authentik version badges.
 */
import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { ThemeClassNames } from "@docusaurus/theme-common";
import { SupportBadge } from "@site/src/components/SupportBadge";
import { VersionBadge } from "@site/src/components/VersionBadge";
import { useSyntheticTitle } from "@site/src/hooks/title";
import type { Props } from "@theme/DocItem/Content";
import Heading from "@theme/Heading";
import MDXContent from "@theme/MDXContent";
import clsx from "clsx";
import React, { useEffect } from "react";

class MarkdownLintError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "MarkdownLintError";
    }
}

const DocItemContent: React.FC<Props> = ({ children }) => {
    const syntheticTitle = useSyntheticTitle();
    const { frontMatter, metadata, contentTitle } = useDoc();
    const {
        // ---
        support_level,
        authentik_version,
        authentik_enterprise,
        authentik_preview,
    } = frontMatter;

    const badges: JSX.Element[] = [];

    if (authentik_version) {
        badges.push(<VersionBadge semver={authentik_version} />);
    }

    if (support_level) {
        badges.push(<SupportBadge level={support_level} />);
    }

    if (authentik_preview) {
        badges.push(<span className="badge badge--preview">Preview</span>);
    }

    if (authentik_enterprise) {
        badges.push(<span className="badge badge--primary">Enterprise</span>);
    }

    if (badges.length && !syntheticTitle) {
        throw new MarkdownLintError(
            `${metadata.id}: ${badges.length} Badge(s) found with a missing synthetic title. Remove the page heading and set it via the frontmatter.`,
        );
    }

    if (frontMatter.title && contentTitle && frontMatter.title === contentTitle) {
        throw new MarkdownLintError(
            `${metadata.id}: Synthetic title "${frontMatter.title}" and content title "${contentTitle}" are the same. Remove the first heading and let the frontmatter set the title.`,
        );
    }

    useEffect(() => {
        const invalidBadges = document.querySelectorAll(`.theme-doc-markdown > header + .badge,
            .theme-doc-markdown .markdown > .badge
            `);

        if (!invalidBadges.length) return;

        console.error(
            `Found ${invalidBadges.length} invalid badges on ${metadata.id}`,
            invalidBadges,
        );

        throw new MarkdownLintError(
            `${metadata.id}: ${invalidBadges.length} Badge(s) defined in markdown content instead of the frontmatter.`,
        );
    }, []);

    return (
        <div className={clsx(ThemeClassNames.docs.docMarkdown, "markdown")}>
            {syntheticTitle ? (
                <header>
                    <Heading as="h1">{syntheticTitle}</Heading>

                    {badges.length ? (
                        <p className="badge-group">
                            {badges.map((badge, index) => (
                                <React.Fragment key={index}>{badge}</React.Fragment>
                            ))}
                        </p>
                    ) : null}
                </header>
            ) : null}

            <MDXContent>{children}</MDXContent>
        </div>
    );
};

export default DocItemContent;
