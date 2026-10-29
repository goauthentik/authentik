import DocTOCContributions from "../../../../components/DocTOCContributions";
import styles from "../../../../components/DocTOC.module.css";

import { useDoc } from "@docusaurus/plugin-content-docs/client";
import DocItemTOCMobile from "@theme-original/DocItem/TOC/Mobile";
import React, { type ReactNode } from "react";

export default function DocItemTOCMobileWrapper(): ReactNode {
    const { toc, frontMatter } = useDoc();
    const hidden = frontMatter.hide_table_of_contents;

    return (
        <div className={hidden ? styles.inlineContributions : styles.mobile}>
            {!hidden && toc.length > 0 ? <DocItemTOCMobile /> : null}
            <DocTOCContributions />
        </div>
    );
}
