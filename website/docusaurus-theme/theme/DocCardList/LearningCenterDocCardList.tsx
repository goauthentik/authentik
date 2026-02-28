import { LEARNING_PATHS } from "../../components/LearningCenter/learningPathsConfig";
import styles from "../../components/LearningCenter/styles.module.css";
import {
    applyLearningCenterFilters,
    type DifficultyLevel,
    type LearningCenterResource,
} from "../utils/learningCenterUtils";
import ErrorBoundary from "./ErrorBoundary";
import LearningPathExperience from "./learningCenter/LearningPathExperience";
import ResourceCard from "./learningCenter/ResourceCard";
import {
    buildLearningResources,
    buildResourceCache,
    buildSidebarItemMap,
    dedupeResourcePool,
} from "./learningCenter/resourceData";
import type { SidebarDocLike } from "./learningCenter/types";
import LearningCenterHelper from "./LearningCenterHelper";

import { useLocation } from "@docusaurus/router";
import type { ReactNode } from "react";
import { useCallback, useMemo } from "react";

interface LearningCenterDocCardListProps {
    resourcePool: SidebarDocLike[];
    className?: string;
}

const LEARNING_PATH_ROUTE_REGEX = /\/learning-center\/path\/([^/]+)/;
const DIFFICULTY_ORDER: Record<DifficultyLevel, number> = {
    beginner: 0,
    intermediate: 1,
    advanced: 2,
};

function getLearningPathFromPathname(pathname: string): string | null {
    const match = pathname.match(LEARNING_PATH_ROUTE_REGEX);
    return match?.[1] ? decodeURIComponent(match[1]) : null;
}

function sortLearningPathResources(resources: LearningCenterResource[]): LearningCenterResource[] {
    return resources.toSorted((a, b) => {
        const difficultyDiff = DIFFICULTY_ORDER[a.difficulty] - DIFFICULTY_ORDER[b.difficulty];
        if (difficultyDiff !== 0) {
            return difficultyDiff;
        }

        const categoryDiff = a.category.localeCompare(b.category);
        if (categoryDiff !== 0) {
            return categoryDiff;
        }

        return a.resourceName.localeCompare(b.resourceName);
    });
}

function groupResourcesByCategory(
    resources: LearningCenterResource[],
): Array<[string, LearningCenterResource[]]> {
    const byCategory = new Map<string, LearningCenterResource[]>();
    resources.forEach((resource) => {
        const category = resource.category || "General";
        const grouped = byCategory.get(category) ?? [];
        grouped.push(resource);
        byCategory.set(category, grouped);
    });

    return Array.from(byCategory.entries())
        .toSorted(([a], [b]) => a.localeCompare(b))
        .map(([category, grouped]) => [
            category,
            grouped.toSorted((a, b) => a.resourceName.localeCompare(b.resourceName)),
        ]);
}

/**
 * Component for rendering learning center resources with search, filtering,
 * and dedicated learning-path pages.
 */
export default function LearningCenterDocCardList({
    resourcePool,
    className,
}: LearningCenterDocCardListProps): ReactNode {
    const pathname = useLocation()?.pathname ?? "";
    const learningPathFromRoute = useMemo(() => getLearningPathFromPathname(pathname), [pathname]);

    const uniqueResourcePool = useMemo(() => dedupeResourcePool(resourcePool), [resourcePool]);
    const resourceCache = useMemo(
        () => buildResourceCache(uniqueResourcePool),
        [uniqueResourcePool],
    );
    const sidebarItemMap = useMemo(
        () => buildSidebarItemMap(uniqueResourcePool),
        [uniqueResourcePool],
    );
    const learningResources = useMemo(
        () => buildLearningResources(uniqueResourcePool, resourceCache),
        [uniqueResourcePool, resourceCache],
    );

    const activeLearningPath = useMemo(
        () => LEARNING_PATHS.find((path) => path.filterTag === learningPathFromRoute) ?? null,
        [learningPathFromRoute],
    );

    const learningPathResources = useMemo(() => {
        if (!learningPathFromRoute) {
            return [];
        }
        return sortLearningPathResources(
            applyLearningCenterFilters(learningResources, {
                selectedLearningPath: learningPathFromRoute,
            }),
        );
    }, [learningResources, learningPathFromRoute]);

    const learningPathTitle = activeLearningPath?.title || "Learning Path";
    const learningPathDescription =
        activeLearningPath?.description ||
        "Follow this curated track to focus on a single area with less distraction.";
    const learningPathDifficulty = activeLearningPath?.difficulty;
    const isLearningPathPage = Boolean(learningPathFromRoute);
    const hasValidLearningPath = Boolean(activeLearningPath);

    const renderResources = useCallback(
        (filteredResources: LearningCenterResource[], searchFilter: string) => {
            const resourcesByCategory = groupResourcesByCategory(filteredResources);

            return (
                <div className={styles.resourceList}>
                    {resourcesByCategory.map(([category, categoryResources]) => {
                        return (
                            <div key={category} className={styles.section}>
                                <h2 className={styles.sectionTitle}>{category}</h2>
                                <div className={styles.resourceGrid}>
                                    {categoryResources.map((resource) => {
                                        const sidebarItem = sidebarItemMap.get(resource.id);
                                        return sidebarItem ? (
                                            <ResourceCard
                                                key={resource.id}
                                                item={sidebarItem}
                                                resourceCache={resourceCache}
                                                searchFilter={searchFilter}
                                            />
                                        ) : null;
                                    })}
                                </div>
                            </div>
                        );
                    })}
                </div>
            );
        },
        [sidebarItemMap, resourceCache],
    );

    return (
        <ErrorBoundary
            fallback={
                <div className="alert alert--warning margin-bottom--md">
                    <h4>Learning Center temporarily unavailable</h4>
                    <p>
                        There was an error loading the learning resources. Please try refreshing the
                        page.
                    </p>
                </div>
            }
        >
            {isLearningPathPage ? (
                <LearningPathExperience
                    className={className}
                    title={learningPathTitle}
                    description={learningPathDescription}
                    difficulty={learningPathDifficulty}
                    resources={learningPathResources}
                    sidebarItemMap={sidebarItemMap}
                    resourceCache={resourceCache}
                    hasValidPath={hasValidLearningPath}
                />
            ) : (
                <LearningCenterHelper
                    resources={learningResources}
                    className={className}
                    learningPaths={LEARNING_PATHS}
                >
                    {renderResources}
                </LearningCenterHelper>
            )}
        </ErrorBoundary>
    );
}
