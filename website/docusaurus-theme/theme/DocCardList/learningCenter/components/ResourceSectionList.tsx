import commonStyles from "../../../../components/LearningCenter/styling/common.module.css";
import type { LearningCenterResource } from "../../../utils/learningCenter/utils";
import ResourceCard from "../ResourceCard";
import type { ResourceCache, SidebarItemMap } from "../types";

interface ResourceSectionListProps {
    resources: LearningCenterResource[];
    sidebarItemMap: SidebarItemMap;
    resourceCache: ResourceCache;
    searchFilter: string;
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

export default function ResourceSectionList({
    resources,
    sidebarItemMap,
    resourceCache,
    searchFilter,
}: ResourceSectionListProps) {
    const resourcesByCategory = groupResourcesByCategory(resources);

    return (
        <div className={commonStyles.resourceList}>
            {resourcesByCategory.map(([category, categoryResources]) => (
                <div key={category} className={commonStyles.section}>
                    <h2 className={commonStyles.sectionTitle}>{category}</h2>
                    <div className={commonStyles.resourceGrid}>
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
            ))}
        </div>
    );
}
