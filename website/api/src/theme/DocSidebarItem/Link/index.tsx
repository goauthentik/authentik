import "./styles.css";

import { useCachedVersionPluginData } from "@goauthentik/docusaurus-theme/components/VersionPicker/utils.ts";

import isInternalUrl from "@docusaurus/isInternalUrl";
import Link from "@docusaurus/Link";
import { isActiveSidebarItem } from "@docusaurus/plugin-content-docs/client";
import { ThemeClassNames } from "@docusaurus/theme-common";
import type { Props } from "@theme/DocSidebarItem/Link";
import IconExternalLink from "@theme/Icon/ExternalLink";
import clsx from "clsx";
import React, { useMemo } from "react";

const DocSidebarItemLink: React.FC<Props> = ({
    item,
    onItemClick,
    activePath,
    level,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    index,
    ...props
}) => {
    const { href, label, className, autoAddBaseUrl } = item;
    const isActive = isActiveSidebarItem(item, activePath);
    const versionPluginData = useCachedVersionPluginData();

    const internalLink = useMemo(() => {
        if (isInternalUrl(href)) return true;

        const inputURL = new URL(href);

        return inputURL.origin === versionPluginData.env.preReleaseOrigin;
    }, [href, versionPluginData.env.apiReferenceOrigin]);

    return (
        <li
            className={clsx(
                ThemeClassNames.docs.docSidebarItemLink,
                ThemeClassNames.docs.docSidebarItemLinkLevel(level),
                "menu__list-item",
                className,
            )}
            key={label}
        >
            <Link
                className={clsx("menu__link", {
                    "menu__link--external": !internalLink,
                    "menu__link--active": isActive,
                })}
                autoAddBaseUrl={autoAddBaseUrl}
                aria-current={isActive ? "page" : undefined}
                to={href}
                {...(internalLink && {
                    onClick: onItemClick ? () => onItemClick(item) : undefined,
                })}
                {...props}
            >
                {item.className?.includes("api-method") ? (
                    <div className="badge-container">
                        <span role="img" className="badge method" />
                    </div>
                ) : null}

                {label}
                {!internalLink && <IconExternalLink />}
            </Link>
        </li>
    );
};

export default DocSidebarItemLink;
