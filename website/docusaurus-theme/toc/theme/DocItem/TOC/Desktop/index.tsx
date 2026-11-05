import styles from "#components/DocTOC.module.css";
import { DocTOCEnabledContext } from "#components/DocTOCContext.ts";
import DocTOCContributions from "#components/DocTOCContributions.tsx";

import { useDoc } from "@docusaurus/plugin-content-docs/client";
import Translate from "@docusaurus/Translate";
import DocItemTOCDesktop from "@theme-init/DocItem/TOC/Desktop";
import React, { type ReactNode, useContext, useEffect, useRef } from "react";

export default function DocItemTOCDesktopWrapper(): ReactNode {
    const { toc, metadata } = useDoc();
    const enabled = useContext(DocTOCEnabledContext);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const list = containerRef.current?.querySelector<HTMLElement>(".theme-doc-toc-desktop");
        if (!enabled || !list) {
            return;
        }

        let previousActiveLink: HTMLElement | null = null;

        const keepActiveLinkVisible = () => {
            const activeLink = list.querySelector<HTMLElement>(".table-of-contents__link--active");
            if (activeLink === previousActiveLink) {
                return;
            }
            previousActiveLink = activeLink;

            if (!activeLink || list.clientHeight === 0) {
                return;
            }

            const listTop = list.getBoundingClientRect().top + list.clientTop;
            const listBottom = listTop + list.clientHeight;
            const linkBounds = activeLink.getBoundingClientRect();

            if (linkBounds.top < listTop) {
                list.scrollTop += linkBounds.top - listTop;
            } else if (linkBounds.bottom > listBottom) {
                list.scrollTop += Math.min(
                    linkBounds.bottom - listBottom,
                    linkBounds.top - listTop,
                );
            }
        };

        const observer = new MutationObserver(keepActiveLinkVisible);
        observer.observe(list, {
            attributes: true,
            attributeFilter: ["class"],
            childList: true,
            subtree: true,
        });
        keepActiveLinkVisible();

        return () => observer.disconnect();
    }, [enabled, metadata.permalink, toc]);

    if (!enabled) {
        return <DocItemTOCDesktop />;
    }

    return (
        <div ref={containerRef} className={`${styles.desktop} thin-scrollbar`}>
            {toc.length > 0 ? (
                <>
                    <h2 className={styles.heading}>
                        <Translate id="docs.toc.heading">On this page</Translate>
                    </h2>
                    <DocItemTOCDesktop />
                </>
            ) : null}
            <DocTOCContributions />
        </div>
    );
}
