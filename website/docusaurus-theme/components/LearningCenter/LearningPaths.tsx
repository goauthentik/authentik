import {
    getDifficultyLabel,
    type LearningCenterResource,
} from "../../theme/utils/learningCenterUtils";
import type { LearningPathDef } from "./learningPathsConfig";
import styles from "./styles.module.css";

import Link from "@docusaurus/Link";
import clsx from "clsx";
import React, { useMemo } from "react";

export interface LearningPathsProps {
    /** Learning path definitions */
    paths: LearningPathDef[];
    /** All available resources to calculate article counts */
    resources: LearningCenterResource[];
}

/**
 * Displays the featured learning paths section at the top of the Learning Center.
 * Shows curated paths with difficulty levels and dynamically calculated article counts.
 * Clicking a path opens a dedicated page for that learning track.
 */
export const LearningPaths: React.FC<LearningPathsProps> = ({ paths, resources }) => {
    const articleCountsByPath = useMemo(() => {
        const counts = new Map<string, number>();
        resources.forEach((resource) => {
            resource.learningPaths.forEach((tag) => {
                counts.set(tag, (counts.get(tag) ?? 0) + 1);
            });
        });
        return counts;
    }, [resources]);

    if (paths.length === 0) return null;

    return (
        <div className={styles.learningPathsSection}>
            <div className={styles.learningPathsHeader}>
                <h2 className={styles.learningPathsTitle}>Learning paths</h2>
            </div>
            <div className={styles.learningPathsList} role="list" aria-label="Learning paths">
                {paths.map((path) => {
                    const articleCount = articleCountsByPath.get(path.filterTag) ?? 0;

                    return (
                        <Link
                            key={path.filterTag}
                            to={`/core/learning-center/path/${path.filterTag}/`}
                            className={styles.learningPathCardLink}
                        >
                            <article className={styles.learningPathCard} role="listitem">
                                <div className={styles.learningPathCardMain}>
                                    <h3 className={styles.learningPathCardTitle}>{path.title}</h3>
                                </div>
                                <div className={styles.learningPathCardMetaColumn}>
                                    <span
                                        className={clsx(
                                            styles.learningPathLevelBadge,
                                            styles[`learningPathLevelBadge-${path.difficulty}`],
                                        )}
                                    >
                                        {getDifficultyLabel(path.difficulty)}
                                    </span>
                                    <span className={styles.learningPathArticleCount}>
                                        {articleCount} article{articleCount !== 1 ? "s" : ""}
                                    </span>
                                </div>
                            </article>
                        </Link>
                    );
                })}
            </div>
        </div>
    );
};

export default LearningPaths;
