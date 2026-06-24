import styles from "./MarkdownPageActions.module.css";

import { useDoc } from "@docusaurus/plugin-content-docs/client";
import Translate from "@docusaurus/Translate";
import React, { type ReactNode } from "react";

export function markdownUrlFromPermalink(permalink: string): string {
    const [path] = permalink.split("#");
    const stripped = (path ?? "").replace(/\/+$/, "");

    if (!stripped) {
        return "/index.md";
    }

    if (stripped.endsWith(".md")) {
        return stripped;
    }

    return `${stripped}.md`;
}

export const MarkdownPageActions: React.FC = (): ReactNode => {
    const { metadata } = useDoc();
    const markdownUrl = markdownUrlFromPermalink(metadata.permalink);

    return (
        <div className={styles.actions}>
            <a className={styles.button} href={markdownUrl} rel="noreferrer" target="_blank">
                <svg
                    aria-hidden="true"
                    className={styles.icon}
                    focusable="false"
                    viewBox="0 0 24 16"
                >
                    <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h15A2.5 2.5 0 0 1 22 2.5v11a2.5 2.5 0 0 1-2.5 2.5h-15A2.5 2.5 0 0 1 2 13.5v-11Zm3.4 10h2V6.85l2.05 2.55 2.05-2.55v5.65h2v-9h-2L9.45 6.05 7.4 3.5h-2v9Zm11.6 0 3-3h-2V3.5h-2v6h-2l3 3Z" />
                </svg>
                <Translate
                    id="theme.common.markdownPageAction"
                    description="The button label to open the current documentation page as Markdown"
                >
                    Markdown
                </Translate>
            </a>
        </div>
    );
};
