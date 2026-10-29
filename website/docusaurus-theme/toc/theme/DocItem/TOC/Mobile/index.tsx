import styles from "#components/DocTOC.module.css";
import { DocTOCEnabledContext } from "#components/DocTOCContext.ts";
import DocTOCContributions from "#components/DocTOCContributions.tsx";

import { useDoc } from "@docusaurus/plugin-content-docs/client";
import DocItemTOCMobile from "@theme-init/DocItem/TOC/Mobile";
import React, { type ReactNode, useContext } from "react";

export default function DocItemTOCMobileWrapper(): ReactNode {
    const { toc, frontMatter } = useDoc();
    const hidden = frontMatter.hide_table_of_contents;
    const enabled = useContext(DocTOCEnabledContext);

    if (!enabled) {
        return <DocItemTOCMobile />;
    }

    return (
        <div className={hidden ? styles.inlineContributions : styles.mobile}>
            {!hidden && toc.length > 0 ? <DocItemTOCMobile /> : null}
            <DocTOCContributions />
        </div>
    );
}
