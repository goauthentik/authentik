import DocTOCContributions from "../../../../components/DocTOCContributions";
import styles from "../../../../components/DocTOC.module.css";

import { useDoc } from "@docusaurus/plugin-content-docs/client";
import Translate from "@docusaurus/Translate";
import DocItemTOCDesktop from "@theme-original/DocItem/TOC/Desktop";
import React, { type ReactNode } from "react";

export default function DocItemTOCDesktopWrapper(): ReactNode {
    const { toc } = useDoc();

    return (
        <div className={`${styles.desktop} thin-scrollbar`}>
            {toc.length > 0 ? (
                <>
                    <h2 className={styles.heading}>
                        <Translate id="docs.toc.heading">
                            On this page
                        </Translate>
                    </h2>
                    <DocItemTOCDesktop />
                </>
            ) : null}
            <DocTOCContributions />
        </div>
    );
}
