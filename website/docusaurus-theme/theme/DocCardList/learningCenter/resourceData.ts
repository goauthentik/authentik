import {
    extractLearningPathsFromProps,
    type LearningCenterResource,
    safeDifficultyExtract,
    safeResourceTypeExtract,
    safeStringArrayExtract,
    safeStringExtract,
} from "../../utils/learningCenterUtils";
import type { ResourceCache, SidebarDocLike, SidebarItemMap } from "./types";

import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";

/**
 * Safely extracts label from sidebar item.
 */
function getLabelFromItem(item: PropSidebarItem): string {
    if ("label" in item && typeof item.label === "string") return item.label;
    return "";
}

/**
 * Removes duplicate sidebar resources by stable key.
 */
export function dedupeResourcePool(resourcePool: SidebarDocLike[]): SidebarDocLike[] {
    const seen = new Set<string>();
    return resourcePool.filter((item) => {
        const key = item.docId || item.href || getLabelFromItem(item);
        if (!key || seen.has(key)) {
            return false;
        }
        seen.add(key);
        return true;
    });
}

/**
 * Builds metadata cache for each docId.
 */
export function buildResourceCache(uniqueResourcePool: SidebarDocLike[]): ResourceCache {
    const cache: ResourceCache = {};

    uniqueResourcePool
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
                learningPaths: extractLearningPathsFromProps(sidebarProps),
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
}

/**
 * Builds O(1) lookup map for sidebar items by docId.
 */
export function buildSidebarItemMap(uniqueResourcePool: SidebarDocLike[]): SidebarItemMap {
    return new Map(uniqueResourcePool.map((item) => [item.docId, item]));
}

/**
 * Converts sidebar metadata into standardized learning resource objects.
 */
export function buildLearningResources(
    uniqueResourcePool: SidebarDocLike[],
    resourceCache: ResourceCache,
): LearningCenterResource[] {
    return uniqueResourcePool
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
                learningPaths: cached.learningPaths,
                shortDescription: cached.shortDescription,
                longDescription: cached.longDescription || undefined,
                difficulty: cached.difficulty,
                resourceType: cached.resourceType,
                estimatedTime: cached.estimatedTime || undefined,
                prerequisites: cached.prerequisites.length > 0 ? cached.prerequisites : undefined,
                relatedResources:
                    cached.relatedResources.length > 0 ? cached.relatedResources : undefined,
            };
        })
        .filter((resource): resource is NonNullable<typeof resource> => resource !== null);
}
