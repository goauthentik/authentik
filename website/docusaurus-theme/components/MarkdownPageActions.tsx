import styles from "./MarkdownPageActions.module.css";

import Translate from "@docusaurus/Translate";
import React, { type ReactNode, useState } from "react";

export function markdownUrlFromPermalink(permalink: string): string {
    try {
        const url = new URL(permalink);
        url.hash = "";
        url.search = "";

        let urlPath = url.pathname;
        while (urlPath.length > 0 && urlPath.endsWith("/")) {
            urlPath = urlPath.slice(0, -1);
        }

        if (!urlPath) {
            url.pathname = "/index.md";
        } else if (!urlPath.endsWith(".md")) {
            url.pathname = `${urlPath}.md`;
        }

        return url.toString();
    } catch {
        // Relative permalinks are handled below.
    }

    const [pathWithQuery] = permalink.split("#");
    const [path] = (pathWithQuery ?? "").split("?");
    let stripped = path ?? "";

    while (stripped.length > 0 && stripped.endsWith("/")) {
        stripped = stripped.slice(0, -1);
    }

    if (!stripped) {
        return "/index.md";
    }

    if (stripped.endsWith(".md")) {
        return stripped;
    }

    return `${stripped}.md`;
}

export const MarkdownPageActions: React.FC = (): ReactNode => {
    const [copied, setCopied] = useState(false);

    const copyMarkdownUrl = async () => {
        try {
            const markdownUrl = markdownUrlFromPermalink(window.location.href);
            await navigator.clipboard.writeText(markdownUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch (error) {
            console.error("Failed to copy Markdown page URL:", error);
        }
    };

    return (
        <div className={styles.actions}>
            <button className={styles.button} onClick={copyMarkdownUrl} type="button">
                <svg
                    aria-hidden="true"
                    className={styles.icon}
                    focusable="false"
                    viewBox="0 0 24 16"
                >
                    <path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h15A2.5 2.5 0 0 1 22 2.5v11a2.5 2.5 0 0 1-2.5 2.5h-15A2.5 2.5 0 0 1 2 13.5v-11Zm3.4 10h2V6.85l2.05 2.55 2.05-2.55v5.65h2v-9h-2L9.45 6.05 7.4 3.5h-2v9Zm11.6 0 3-3h-2V3.5h-2v6h-2l3 3Z" />
                </svg>
                {copied ? (
                    <Translate
                        id="theme.common.markdownPageAction.copied"
                        description="The button label shown after the Markdown URL is copied"
                    >
                        Copied
                    </Translate>
                ) : (
                    <Translate
                        id="theme.common.markdownPageAction.copy"
                        description="The button label to copy the current documentation page's Markdown URL"
                    >
                        Copy Markdown link
                    </Translate>
                )}
            </button>
        </div>
    );
};
