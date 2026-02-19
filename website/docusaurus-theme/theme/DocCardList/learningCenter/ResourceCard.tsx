import styles from "../../../components/LearningCenter/styles.module.css";
import { getDifficultyLabel } from "../../utils/learningCenterUtils";
import type { ResourceCache, SidebarDocLike } from "./types";

import Link from "@docusaurus/Link";
import clsx from "clsx";
import React from "react";

/**
 * Highlights matching search terms in text.
 */
function highlightText(
    text: string,
    searchFilter: string,
    keyPrefix: string,
): (string | React.ReactElement)[] {
    if (!searchFilter) return [text];

    const escaped = searchFilter.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`(${escaped})`, "gi");
    const matches = text.split(regex);

    return matches.map((part, i) => {
        if (part.toLowerCase() === searchFilter.toLowerCase()) {
            return (
                <mark key={`${keyPrefix}-${i}`} className={styles.searchHighlight}>
                    {part}
                </mark>
            );
        }
        return part;
    });
}

export interface ResourceCardProps {
    item: SidebarDocLike;
    resourceCache: ResourceCache;
    searchFilter?: string;
    pathStepNumber?: number;
}

/**
 * Renders a single learning resource card that links to the article page.
 */
export function ResourceCard({
    item,
    resourceCache,
    searchFilter = "",
    pathStepNumber,
}: ResourceCardProps) {
    const cachedData = item.docId ? resourceCache[item.docId] : null;

    if (!item.docId || !cachedData) {
        return null;
    }

    const { resourceName, shortDescription, difficulty, estimatedTime } = cachedData;
    const articleHref = item.href || "";
    if (!articleHref) {
        return null;
    }

    return (
        <Link to={articleHref} className={styles.resourceCardLink}>
            <article className={styles.resourceCard}>
                {pathStepNumber ? (
                    <span className={styles.pathStepBadge}>Step {pathStepNumber}</span>
                ) : null}
                <div className={styles.resourceCardHeader}>
                    <h3 className={styles.resourceTitle}>
                        {highlightText(resourceName, searchFilter, "title")}
                    </h3>
                </div>

                <div className={styles.resourceMeta}>
                    <span
                        className={clsx(styles.badge, styles.difficultyBadge, styles[difficulty])}
                    >
                        {getDifficultyLabel(difficulty)}
                    </span>
                    {estimatedTime ? (
                        <span className={clsx(styles.badge, styles.timeBadge)}>
                            <svg
                                width="12"
                                height="12"
                                viewBox="0 0 16 16"
                                fill="currentColor"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <path d="M8 0a8 8 0 110 16A8 8 0 018 0zm0 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM8 3a.75.75 0 01.75.75v3.69l2.28 2.28a.75.75 0 11-1.06 1.06l-2.5-2.5A.75.75 0 017.25 8V3.75A.75.75 0 018 3z" />
                            </svg>
                            {estimatedTime}
                        </span>
                    ) : null}
                </div>

                <p className={styles.resourceShort}>
                    {shortDescription
                        ? highlightText(shortDescription, searchFilter, "short")
                        : "Description not provided."}
                </p>
            </article>
        </Link>
    );
}

export default ResourceCard;
