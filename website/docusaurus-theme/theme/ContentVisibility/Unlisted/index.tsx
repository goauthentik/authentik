import {
    ThemeClassNames,
    UnlistedBannerMessage,
    UnlistedBannerTitle,
    UnlistedMetadata,
} from "@docusaurus/theme-common";
import Admonition from "@theme/Admonition";
import type { Props } from "@theme/ContentVisibility/Unlisted";
import clsx from "clsx";
import React, { type ReactNode } from "react";

export function UnlistedBanner({ className }: Props) {
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

export default function Unlisted(): ReactNode {
    return <UnlistedMetadata />;
}
