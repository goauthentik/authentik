import type {
    DifficultyLevel,
    LearningCenterResource,
} from "../../theme/utils/learningCenterUtils";
import styles from "./styles.module.css";

import clsx from "clsx";
import React from "react";

/**
 * Definition for a learning path shown in the featured section
 */
export interface LearningPathDef {
    /** Display title for the learning path */
    title: string;
    /** Tag used to filter articles belonging to this path */
    filterTag: string;
    /** Difficulty level for display */
    difficulty: DifficultyLevel;
}

export interface LearningPathsProps {
    /** Learning path definitions */
    paths: LearningPathDef[];
    /** All available resources to calculate article counts */
    resources: LearningCenterResource[];
    /** Currently selected learning path tag (if any) */
    selectedPath: string | null;
    /** Callback when a learning path is selected */
    onSelectPath: (filterTag: string | null) => void;
}

/**
 * Displays the featured learning paths section at the top of the Learning Center.
 * Shows curated paths with difficulty levels and dynamically calculated article counts.
 * Clicking a path filters the articles below.
 */
export const LearningPaths: React.FC<LearningPathsProps> = ({
    paths,
    resources,
    selectedPath,
    onSelectPath,
}) => {
    if (paths.length === 0) return null;

    // Calculate article counts for each path based on learningPaths field
    const getArticleCount = (filterTag: string): number => {
        return resources.filter((r) => r.learningPaths.includes(filterTag)).length;
    };

    const handlePathClick = (filterTag: string) => {
        // Toggle: if already selected, deselect; otherwise select
        if (selectedPath === filterTag) {
            onSelectPath(null);
        } else {
            onSelectPath(filterTag);
        }
    };

    return (
        <div className={styles.learningPathsSection}>
            <h2 className={styles.learningPathsTitle}>Learning Paths</h2>
            <div className={styles.learningPathsList}>
                {paths.map((path) => {
                    const articleCount = getArticleCount(path.filterTag);
                    const isSelected = selectedPath === path.filterTag;

                    return (
                        <div
                            key={path.filterTag}
                            className={clsx(
                                styles.learningPathRow,
                                isSelected && styles.learningPathRowSelected,
                            )}
                        >
                            <button
                                type="button"
                                className={clsx(
                                    styles.learningPathLink,
                                    isSelected && styles.learningPathLinkSelected,
                                )}
                                onClick={() => handlePathClick(path.filterTag)}
                            >
                                {path.title}
                            </button>
                            <div className={styles.learningPathMeta}>
                                <span
                                    className={clsx(
                                        styles.learningPathBadge,
                                        styles[`learningPathBadge-${path.difficulty}`],
                                    )}
                                >
                                    {path.difficulty.charAt(0).toUpperCase() +
                                        path.difficulty.slice(1)}
                                </span>
                                <span className={styles.learningPathCount}>
                                    {articleCount} article{articleCount !== 1 ? "s" : ""}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
            {selectedPath && (
                <button
                    type="button"
                    className={styles.clearPathButton}
                    onClick={() => onSelectPath(null)}
                >
                    Clear path filter
                </button>
            )}
        </div>
    );
};

export default LearningPaths;
