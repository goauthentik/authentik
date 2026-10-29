import DocItemLayout from "../../DocItem/Layout/index";

import { DocTOCEnabledContext } from "#components/DocTOCContext.ts";

import { useDoc } from "@docusaurus/plugin-content-docs/client";
import ApiItemLayout from "@theme-init/ApiItem/Layout";
import type { Props } from "@theme/DocItem/Layout";
import React, { type ReactNode } from "react";

const apiGuideIDs = new Set(["index", "authentication", "flow-executor", "websocket", "clients"]);

export default function ApiItemLayoutWrapper(props: Props): ReactNode {
    const { metadata } = useDoc();
    const enabled = apiGuideIDs.has(metadata.id);

    return (
        <DocTOCEnabledContext.Provider value={enabled}>
            {enabled ? <DocItemLayout {...props} /> : <ApiItemLayout {...props} />}
        </DocTOCEnabledContext.Provider>
    );
}
