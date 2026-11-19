/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

/**
 * @file Ejected from `@docusaurus/theme-classic` 3.10.2 `DocItem/Footer`.
 *   The edit link moved into the contribution links, so this footer never
 *   passes `editUrl` to `EditMetaRow`, and an `editUrl` alone no longer
 *   renders it. Upstream would leave an empty footer with a top margin on
 *   every page.
 */

import { useDoc } from "@docusaurus/plugin-content-docs/client";
import { ThemeClassNames } from "@docusaurus/theme-common";
import EditMetaRow from "@theme/EditMetaRow";
import TagsListInline from "@theme/TagsListInline";
import clsx from "clsx";
import React, { type ReactNode } from "react";

export default function DocItemFooter(): ReactNode {
    const { metadata } = useDoc();
    const { lastUpdatedAt, lastUpdatedBy, tags } = metadata;

    const canDisplayTagsRow = tags.length > 0;
    const canDisplayEditMetaRow = !!(lastUpdatedAt || lastUpdatedBy);

    if (!canDisplayTagsRow && !canDisplayEditMetaRow) {
        return null;
    }

    return (
        <footer className={clsx(ThemeClassNames.docs.docFooter, "docusaurus-mt-lg")}>
            {canDisplayTagsRow ? (
                <div className={clsx("row margin-top--sm", ThemeClassNames.docs.docFooterTagsRow)}>
                    <div className="col">
                        <TagsListInline tags={tags} />
                    </div>
                </div>
            ) : null}
            {canDisplayEditMetaRow ? (
                <EditMetaRow
                    className={clsx("margin-top--sm", ThemeClassNames.docs.docFooterEditMetaRow)}
                    editUrl={null}
                    lastUpdatedAt={lastUpdatedAt}
                    lastUpdatedBy={lastUpdatedBy}
                />
            ) : null}
        </footer>
    );
}
