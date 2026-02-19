import styles from "../../../components/LearningCenter/styles.module.css";
import {
    type DifficultyLevel,
    getDifficultyLabel,
    type LearningCenterResource,
} from "../../utils/learningCenterUtils";
import ResourceCard from "./ResourceCard";
import type { ResourceCache, SidebarItemMap } from "./types";

import Link from "@docusaurus/Link";
import clsx from "clsx";
import React from "react";

export interface LearningPathExperienceProps {
    className?: string;
    title: string;
    description: string;
    difficulty?: DifficultyLevel;
    resources: LearningCenterResource[];
    sidebarItemMap: SidebarItemMap;
    resourceCache: ResourceCache;
    hasValidPath: boolean;
}

/**
 * Dedicated, focused learning-path page content.
 */
export function LearningPathExperience({
    className,
    title,
    description,
    difficulty,
    resources,
    sidebarItemMap,
    resourceCache,
    hasValidPath,
}: LearningPathExperienceProps) {
    return (
        <div className={clsx(styles.learningPathExperience, className)}>
            <Link className={styles.pathBackLink} to="/core/learning-center/">
                Back to Learning Center
            </Link>

            <section className={styles.pathHero}>
                <p className={styles.pathHeroEyebrow}>Learning Path</p>
                <h1 className={styles.pathHeroTitle}>{title}</h1>
                <p className={styles.pathHeroDescription}>{description}</p>
                <div className={styles.pathHeroMeta}>
                    {difficulty ? (
                        <span
                            className={clsx(
                                styles.pathHeroMetaItem,
                                styles[`pathHeroMetaItemDifficulty-${difficulty}`],
                            )}
                        >
                            {getDifficultyLabel(difficulty)}
                        </span>
                    ) : null}
                    <span className={styles.pathHeroMetaItem}>
                        {resources.length} article{resources.length !== 1 ? "s" : ""}
                    </span>
                </div>
            </section>

            {!hasValidPath ? (
                <div className="alert alert--warning margin-bottom--md">
                    Unknown learning path. Please return to the Learning Center and choose a valid
                    track.
                </div>
            ) : null}

            {resources.length > 0 ? (
                <section className={styles.pathCurriculumSection}>
                    <h2 className={styles.pathCurriculumTitle}>Path Curriculum</h2>
                    <div className={styles.resourceGrid}>
                        {resources.map((resource, index) => {
                            const sidebarItem = sidebarItemMap.get(resource.id);
                            return sidebarItem ? (
                                <ResourceCard
                                    key={resource.id}
                                    item={sidebarItem}
                                    resourceCache={resourceCache}
                                    pathStepNumber={index + 1}
                                />
                            ) : null;
                        })}
                    </div>
                </section>
            ) : null}
        </div>
    );
}

export default LearningPathExperience;
