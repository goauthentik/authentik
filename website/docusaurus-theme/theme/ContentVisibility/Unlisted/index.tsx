import { useDoc } from "@docusaurus/plugin-content-docs/client";
import {
    ThemeClassNames,
    UnlistedBannerMessage,
    UnlistedBannerTitle,
    UnlistedMetadata,
} from "@docusaurus/theme-common";
import Translate from "@docusaurus/Translate";
import Admonition from "@theme/Admonition";
import type { Props } from "@theme/ContentVisibility/Unlisted";
import clsx from "clsx";
import React, { type ReactNode } from "react";

function UnlistedBanner({ className }: Props) {
    const context = useDoc();

    if (context.metadata.id?.startsWith("releases")) {
        return (
            <Admonition
                type="note"
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
                <Translate
                    id="theme.contentVisibility.unlistedBanner.preRelease.message"
                    description="The unlisted content banner message"
                >
                    This documentation is for an upcoming version of authentik. It may be incomplete
                    or subject to changes before the final release.
                </Translate>
            </Admonition>
        );
    }

    return (
        <Admonition
            type="caution"
            title={<UnlistedBannerTitle />}
            className={clsx(className, ThemeClassNames.common.unlistedBanner)}
        >
            <UnlistedBannerMessage />
        </Admonition>
    );
}

export default function Unlisted(props: Props): ReactNode {
    return (
        <>
            <UnlistedMetadata />
            <UnlistedBanner {...props} />
        </>
    );
}
