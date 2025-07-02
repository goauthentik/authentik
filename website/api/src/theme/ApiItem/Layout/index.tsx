import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { useWindowSize } from "@docusaurus/theme-common";
import type { Props } from "@theme/ApiItem/Layout";
import ContentVisibility from "@theme/ContentVisibility";
import DocBreadcrumbs from "@theme/DocBreadcrumbs";
import DocItemContent from "@theme/DocItem/Content";
import DocItemFooter from "@theme/DocItem/Footer";
import DocItemPaginator from "@theme/DocItem/Paginator";
import DocItemTOCDesktop from "@theme/DocItem/TOC/Desktop";
import DocItemTOCMobile from "@theme/DocItem/TOC/Mobile";
import DocVersionBadge from "@theme/DocVersionBadge";
import DocVersionBanner from "@theme/DocVersionBanner";
import clsx from "clsx";
import React, { type JSX } from "react";

import styles from "./styles.module.css";

/**
 * Decide if the toc should be rendered, on mobile or desktop viewports
 */
function useDocTOC() {
    const { frontMatter, toc } = useDoc();
    const windowSize = useWindowSize();

    const hidden = frontMatter.hide_table_of_contents;
    const canRender = !hidden && toc.length > 0;

    const mobile = canRender ? <DocItemTOCMobile /> : undefined;

    const desktop =
        canRender && (windowSize === "desktop" || windowSize === "ssr") ? (
            <DocItemTOCDesktop />
        ) : undefined;

    return {
        hidden,
        mobile,
        desktop,
    };
}

export default function DocItemLayout({ children }: Props): JSX.Element {
    const docTOC = useDocTOC();
    const { metadata, frontMatter } = useDoc() as DocContextValue;
    const { api, schema } = frontMatter;

    return (
        <div className="row">
            <div className={clsx("col", !docTOC.hidden && styles.docItemCol)}>
                <ContentVisibility metadata={metadata} />
                <DocVersionBanner />
                <div className={styles.docItemContainer}>
                    <article>
                        <DocBreadcrumbs />
                        <DocVersionBadge />
                        {docTOC.mobile}
                        <DocItemContent>{children}</DocItemContent>
                        <div className="row">
                            <div className={clsx("col", api || schema ? "col--7" : "col--12")}>
                                <DocItemFooter />
                            </div>
                        </div>
                    </article>
                    <div className="row">
                        <div className={clsx("col", api || schema ? "col--7" : "col--12")}>
                            <DocItemPaginator />
                        </div>
                    </div>
                </div>
            </div>

            {docTOC.desktop ? <div className="col col--3">{docTOC.desktop}</div> : null}
        </div>
    );
}
