/**
 * @file Gives the hand-written API guides the shared docs layout, with its
 *   TOC and contribution links, while generated reference pages keep the
 *   OpenAPI theme's layout.
 */

import { DocTOCEnabledContext } from "@goauthentik/docusaurus-theme/components/DocTOCContext.ts";

import { useDoc } from "@docusaurus/plugin-content-docs/client";
import ApiItemLayout from "@theme-original/ApiItem/Layout";
import DocItemLayout, { type Props } from "@theme/DocItem/Layout";
import React, { type ReactNode } from "react";

export default function ApiItemLayoutWrapper(props: Props): ReactNode {
    const { metadata } = useDoc();

    // Keep in sync with `editUrl` in docusaurus.config.esm.mjs. Generated pages
    // can't be told apart by front matter: the info page has neither `api` nor
    // `schema`.
    if (!metadata.id.startsWith("reference/")) {
        return <DocItemLayout {...props} />;
    }

    return (
        <DocTOCEnabledContext.Provider value={false}>
            <ApiItemLayout {...props} />
        </DocTOCEnabledContext.Provider>
    );
}
