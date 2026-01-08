import styles from "../../components/LearningCenter/styles.module.css";
import { formatCategory, formatTag } from "../../components/LearningCenter/utils";
import {
    type DifficultyLevel,
    getDifficultyLabel,
    getResourceTypeLabel,
    type LearningCenterResource,
    type ResourceType,
    safeDifficultyExtract,
    safeResourceTypeExtract,
    safeStringArrayExtract,
    safeStringExtract,
} from "../utils/learningCenterUtils";
import ErrorBoundary from "./ErrorBoundary";
import LearningCenterHelper from "./LearningCenterHelper";

import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";
import clsx from "clsx";
import React, { ReactNode, useCallback, useMemo } from "react";

type SidebarDocLike = Extract<PropSidebarItem, { type: "link" }>;

interface LearningCenterDocCardListProps {
    resourcePool: SidebarDocLike[];
    className?: string;
}

/**
 * Cache structure for resource data - key is guaranteed to be a string docId
 */
interface ResourceCache {
    [docId: string]: {
        resourceName: string;
        category: string;
        tags: string[];
        shortDescription: string;
        longDescription: string;
        difficulty: DifficultyLevel;
        resourceType: ResourceType;
        estimatedTime: string;
        prerequisites: string[];
        relatedResources: string[];
    };
}

/**
 * Safely extracts label from sidebar item
 */
function getLabelFromItem(item: PropSidebarItem): string {
    if ("label" in item && typeof item.label === "string") return item.label;
    return "";
}

/**
 * Highlights matching search terms in text
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

/**
 * Renders a single learning resource as a clickable card that links to the article page
 */
function ResourceCard({
    item,
    resourceCache,
    searchFilter = "",
}: {
    item: SidebarDocLike;
    resourceCache: ResourceCache;
    searchFilter?: string;
}) {
    const cachedData = item.docId ? resourceCache[item.docId] : null;

    if (!item.docId || !cachedData) {
        return null;
    }

    const {
        resourceName,
        category,
        tags,
        shortDescription,
        difficulty,
        resourceType,
        estimatedTime,
    } = cachedData;

    // Link to the article page
    const articleHref = item.href || "";

    return (
        <a href={articleHref} className={styles.resourceCardLink}>
            <article className={styles.resourceCard}>
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
                    {estimatedTime && (
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
                    )}
                </div>

                <p className={styles.resourceShort}>
                    {shortDescription
                        ? highlightText(shortDescription, searchFilter, "short")
                        : "Description not provided."}
                </p>

                {tags.length > 0 && (
                    <div className={styles.resourceTags}>
                        {tags.map((tag) => (
                            <span key={tag} className={styles.tagChip}>
                                {formatTag(tag)}
                            </span>
                        ))}
                    </div>
                )}
            </article>
        </a>
    );
}

/**
 * Component for rendering learning center resources with search, filtering, and view modes.
 */
export default function LearningCenterDocCardList({
    resourcePool,
    className,
}: LearningCenterDocCardListProps): ReactNode {
    // Build resource cache from sidebar customProps
    const resourceCache = useMemo<ResourceCache>(() => {
        const cache: ResourceCache = {};

        resourcePool
            .filter((item): item is SidebarDocLike & { docId: string } => Boolean(item.docId))
            .forEach((item) => {
                const sidebarProps = item.customProps ?? {};
                const fallbackLabel = getLabelFromItem(item);

                cache[item.docId] = {
                    resourceName:
                        safeStringExtract(sidebarProps.resourceName) ||
                        fallbackLabel ||
                        item.docId ||
                        "Resource",
                    category: safeStringExtract(sidebarProps.category, "General"),
                    tags: safeStringArrayExtract(sidebarProps.tags),
                    shortDescription: safeStringExtract(sidebarProps.shortDescription),
                    longDescription: safeStringExtract(sidebarProps.longDescription),
                    difficulty: safeDifficultyExtract(sidebarProps.difficulty),
                    resourceType: safeResourceTypeExtract(sidebarProps.resourceType),
                    estimatedTime: safeStringExtract(sidebarProps.estimatedTime),
                    prerequisites: safeStringArrayExtract(sidebarProps.prerequisites),
                    relatedResources: safeStringArrayExtract(sidebarProps.relatedResources),
                };
            });

        return cache;
    }, [resourcePool]);

    // O(1) lookup map for sidebar items by docId
    const sidebarItemMap = useMemo(
        () => new Map(resourcePool.map((item) => [item.docId, item])),
        [resourcePool],
    );

    // Transform cached data to LearningCenterResource format
    const learningResources = useMemo<LearningCenterResource[]>(() => {
        return resourcePool
            .filter((item): item is SidebarDocLike & { docId: string } => Boolean(item.docId))
            .map((item) => {
                const cached = resourceCache[item.docId];
                if (!cached) {
                    return null;
                }
                return {
                    id: item.docId,
                    resourceName: cached.resourceName,
                    category: cached.category,
                    tags: cached.tags,
                    shortDescription: cached.shortDescription,
                    longDescription: cached.longDescription || undefined,
                    difficulty: cached.difficulty,
                    resourceType: cached.resourceType,
                    estimatedTime: cached.estimatedTime || undefined,
                    prerequisites:
                        cached.prerequisites.length > 0 ? cached.prerequisites : undefined,
                    relatedResources:
                        cached.relatedResources.length > 0 ? cached.relatedResources : undefined,
                };
            })
            .filter((resource): resource is NonNullable<typeof resource> => resource !== null);
    }, [resourcePool, resourceCache]);

    // Render function for resources - simple grid view
    const renderResources = useCallback(
        (filteredResources: LearningCenterResource[], searchFilter: string) => {
            return (
                <div className={styles.resourceGrid}>
                    {filteredResources.map((resource) => {
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
            <LearningCenterHelper resources={learningResources} className={className}>
                {renderResources}
            </LearningCenterHelper>
        </ErrorBoundary>
    );
}
