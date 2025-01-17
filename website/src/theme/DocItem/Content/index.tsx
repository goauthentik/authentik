/**
 * @file Swizzled DocItemContent component.
 *
 * This component is a swizzled version of the original DocItemContent component.
 *
 * Similar to Docusaurus' default `DocItemContent`, this component renders
 * the content of a documentation page. However, it also adds support for
 * support badges, and Authentik version badges.
 */

import React from "react";
import clsx from "clsx";
import { ThemeClassNames } from "@docusaurus/theme-common";
import {
    DocContextValue,
    useDoc,
} from "@docusaurus/plugin-content-docs/client";
import Heading from "@theme/Heading";
import MDXContent from "@theme/MDXContent";
import type { Props } from "@theme/DocItem/Content";
import { DocFrontMatter } from "@docusaurus/plugin-content-docs";
import { useSyntheticTitle } from "@site/src/hooks/title";
import { SupportBadge } from "@site/src/components/SupportBadge";
import { VersionBadge } from "@site/src/components/VersionBadge";

interface SwizzledDocFrontMatter extends DocFrontMatter {
    support_level?: string;
    authentik_version?: string;
    authentik_preview: boolean;
    authentik_enterprise: boolean;
}

interface SwizzledDocContextValue extends DocContextValue {
    frontMatter: SwizzledDocFrontMatter;
}

const DocItemContent: React.FC<Props> = ({ children }) => {
    const syntheticTitle = useSyntheticTitle();
    const { frontMatter } = useDoc() as SwizzledDocContextValue;
    const {
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

    return (
        <div className={clsx(ThemeClassNames.docs.docMarkdown, "markdown")}>
            {syntheticTitle ? (
                <header>
                    <Heading as="h1">{syntheticTitle}</Heading>

                    {badges.length ? (
                        <p className="badge-group">
                            {badges.map((badge, index) => (
                                <React.Fragment key={index}>
                                    {badge}
                                </React.Fragment>
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
