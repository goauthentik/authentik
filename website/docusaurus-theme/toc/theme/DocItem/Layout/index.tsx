/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

/**
 * @file Ejected from `@docusaurus/theme-classic` 3.10.2 `DocItem/Layout`,
 *   since a wrapper cannot render the TOC column for a page without headings.
 *   Diff against upstream when bumping Docusaurus. The differences:
 *
 *   - The TOC column renders whenever `hide_table_of_contents` is unset, not only when the page has
 *     headings, so the contribution links in it show on every page.
 *   - The row is a CSS grid whose TOC column matches the sidebar width, in place of `col--3`, and the
 *     content column drops `docItemCol`.
 *   - The contribution links also render after the article, where narrow viewports and pages that
 *     hide the TOC show them.
 *   - The mobile TOC is wrapped so `DocTOC.module.css` can style its links.
 */

import styles from "./styles.module.css";

import tocStyles from "#components/DocTOC.module.css";
import DocTOCContributions from "#components/DocTOCContributions.tsx";

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
    const { metadata, frontMatter, toc } = useDoc();
    const windowSize = useWindowSize();
    const hidden = frontMatter.hide_table_of_contents;
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
                        {!hidden && toc.length > 0 ? (
                            <div className={tocStyles.mobile}>
                                <DocItemTOCMobile />
                            </div>
                        ) : null}
                        <DocItemContent>{children}</DocItemContent>
                        <DocItemFooter />
                    </article>
                    <div className={styles.articleContributions}>
                        <DocTOCContributions />
                    </div>
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
