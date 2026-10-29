/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

import styles from "./styles.module.css";

import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { useWindowSize } from "@docusaurus/theme-common";
import ContentVisibility from "@theme/ContentVisibility";
import DocBreadcrumbs from "@theme/DocBreadcrumbs";
import DocItemContent from "@theme/DocItem/Content";
import DocItemFooter from "@theme/DocItem/Footer";
import type { Props } from "@theme/DocItem/Layout";
import DocItemPaginator from "@theme/DocItem/Paginator";
import DocItemTOCDesktop from "@theme/DocItem/TOC/Desktop";
import DocItemTOCMobile from "@theme/DocItem/TOC/Mobile";
import DocVersionBadge from "@theme/DocVersionBadge";
import DocVersionBanner from "@theme/DocVersionBanner";
import clsx from "clsx";
import React, { type ReactNode } from "react";

export default function DocItemLayout({ children }: Props): ReactNode {
    const { metadata, frontMatter } = useDoc();
    const windowSize = useWindowSize();
    const hidden = frontMatter.hide_table_of_contents;
    // Unlike the upstream layout, retain contribution links even without headings.
    const desktop = !hidden && (windowSize === "desktop" || windowSize === "ssr");

    return (
        <div className={clsx("row", styles.docItemRow, !hidden && styles.withTOC)}>
            <div className="col">
                <ContentVisibility metadata={metadata} />
                <DocVersionBanner />
                <div className={styles.docItemContainer}>
                    <article>
                        <DocBreadcrumbs />
                        <DocVersionBadge />
                        <DocItemTOCMobile />
                        <DocItemContent>{children}</DocItemContent>
                        <DocItemFooter />
                    </article>
                    <DocItemPaginator />
                </div>
            </div>
            {desktop ? (
                <div className="col">
                    <DocItemTOCDesktop />
                </div>
            ) : null}
        </div>
    );
}
