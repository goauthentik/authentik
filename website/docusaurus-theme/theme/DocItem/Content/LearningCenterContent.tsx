/**
 * Renders learning center resource frontmatter as nicely formatted content.
 */

import styles from "./LearningCenterContent.module.css";

import React from "react";

export type DifficultyLevel = "beginner" | "intermediate" | "advanced";

export interface LearningCenterContentProps {
    learningPaths?: string[];
    shortDescription: string;
    difficulty: DifficultyLevel;
    estimatedTime?: string;
}

const difficultyLabels: Record<DifficultyLevel, string> = {
    beginner: "Beginner",
    intermediate: "Intermediate",
    advanced: "Advanced",
};

const ClockIcon: React.FC = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ marginRight: "0.25rem" }}
    >
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
    </svg>
);

export const LearningCenterContent: React.FC<LearningCenterContentProps> = ({
    learningPaths,
    shortDescription,
    difficulty,
    estimatedTime,
}) => {
    return (
        <div className={styles.learningCenterContent}>
            <div className={styles.meta}>
                <span className={`${styles.difficultyBadge} ${styles[difficulty]}`}>
                    {difficultyLabels[difficulty]}
                </span>
                {estimatedTime ? (
                    <span className={styles.timeBadge}>
                        <ClockIcon />
                        {estimatedTime}
                    </span>
                ) : null}
            </div>

            <p className={styles.shortDescription}>{shortDescription}</p>

            {learningPaths && learningPaths.length > 0 ? (
                <div className={styles.tags}>
                    {learningPaths.map((learningPath) => (
                        <span key={learningPath} className={styles.tagChip}>
                            {learningPath}
                        </span>
                    ))}
                </div>
            ) : null}
        </div>
    );
};

export default LearningCenterContent;
