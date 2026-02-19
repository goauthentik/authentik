import type {
    DifficultyLevel,
    LearningCenterResource,
    ResourceType,
} from "../../utils/learningCenterUtils";

import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";

export type SidebarDocLike = Extract<PropSidebarItem, { type: "link" }>;

export interface ResourceCacheEntry {
    resourceName: string;
    category: string;
    learningPaths: string[];
    shortDescription: string;
    longDescription: string;
    difficulty: DifficultyLevel;
    resourceType: ResourceType;
    estimatedTime: string;
    prerequisites: string[];
    relatedResources: string[];
}

export type ResourceCache = Record<string, ResourceCacheEntry>;

export type SidebarItemMap = Map<SidebarDocLike["docId"], SidebarDocLike>;

export type LearningResourceList = LearningCenterResource[];
