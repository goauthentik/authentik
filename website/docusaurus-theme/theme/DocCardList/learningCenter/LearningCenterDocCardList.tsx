import { LEARNING_PATHS } from "../../../components/LearningCenter/learningPathsConfig";
import commonStyles from "../../../components/LearningCenter/styling/common.module.css";
import {
    applyLearningCenterFilters,
    type DifficultyLevel,
    type LearningCenterResource,
} from "../../utils/learningCenter/utils";
import ErrorBoundary from "../ErrorBoundary";
import ResourceSectionList from "./components/ResourceSectionList";
import LearningCenterHelper from "./LearningCenterHelper";
import LearningCenterLanding from "./LearningCenterLanding";
import LearningPathExperience from "./LearningPathExperience";
import { consumeLearningCenterNavigationState } from "./navigationState";
import {
    buildLearningResources,
    buildResourceCache,
    buildSidebarItemMap,
    dedupeResourcePool,
} from "./resourceData";
import type { SidebarDocLike } from "./types";

import { useLocation } from "@docusaurus/router";
import clsx from "clsx";
import type { ReactNode } from "react";
import { useCallback, useMemo } from "react";

interface LearningCenterDocCardListProps {
    resourcePool: SidebarDocLike[];
    className?: string;
}

const LEARNING_PATH_ROUTE_REGEX = /\/learning-center\/path\/([^/]+)/;
const LEARNING_CENTER_ARTICLES_ROUTE_REGEX = /\/learning-center\/articles\/?$/;
const LEARNING_CENTER_INDEX_ROUTE_REGEX = /\/learning-center\/?$/;
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

/**
 * Component for rendering learning center resources with search, filtering,
 * and dedicated learning-path pages.
 */
export default function LearningCenterDocCardList({
    resourcePool,
    className,
}: LearningCenterDocCardListProps): ReactNode {
    const location = useLocation();
    const pathname = location?.pathname ?? "";
    const learningPathFromRoute = useMemo(() => getLearningPathFromPathname(pathname), [pathname]);
    const isLearningCenterArticlesPage = useMemo(
        () => LEARNING_CENTER_ARTICLES_ROUTE_REGEX.test(pathname),
        [pathname],
    );
    const isLearningCenterIndexPage = useMemo(
        () => LEARNING_CENTER_INDEX_ROUTE_REGEX.test(pathname),
        [pathname],
    );
    const initialNavigationState = useMemo(
        () => (isLearningCenterArticlesPage ? consumeLearningCenterNavigationState() : {}),
        [isLearningCenterArticlesPage],
    );

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
    const articlesPageResources = useMemo(() => {
        if (!isLearningCenterArticlesPage) {
            return [];
        }

        return applyLearningCenterFilters(learningResources, {
            query: initialNavigationState.filter,
            selectedCategories: initialNavigationState.categories,
            selectedDifficulty: initialNavigationState.difficulty,
        });
    }, [isLearningCenterArticlesPage, learningResources, initialNavigationState]);

    const renderResources = useCallback(
        (filteredResources: LearningCenterResource[], searchFilter: string) => {
            return (
                <ResourceSectionList
                    resources={filteredResources}
                    sidebarItemMap={sidebarItemMap}
                    resourceCache={resourceCache}
                    searchFilter={searchFilter}
                />
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
            ) : isLearningCenterIndexPage ? (
                <LearningCenterLanding
                    resources={learningResources}
                    learningPaths={LEARNING_PATHS}
                />
            ) : isLearningCenterArticlesPage ? (
                <div className={clsx(commonStyles.learningCenter, className)}>
                    {renderResources(articlesPageResources, initialNavigationState.filter ?? "")}
                </div>
            ) : (
                <LearningCenterHelper resources={learningResources} className={className}>
                    {renderResources}
                </LearningCenterHelper>
            )}
        </ErrorBoundary>
    );
}
