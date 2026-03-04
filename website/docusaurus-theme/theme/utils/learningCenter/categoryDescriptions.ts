/**
 * Category descriptions loaded from _category_.json files.
 * Import category metadata and export descriptions for use in components.
 *
 * Keep this list in sync when adding new learning-center categories.
 */

import customizeYourInstance from "../../../../docs/core/learning-center/customize-your-instance/_category_.json";

export interface CategoryMetadata {
    label: string;
    position: number;
    description?: string;
}

/**
 * Map of category names to their metadata from _category_.json files.
 * Add new categories here as they are created.
 */
const categoryMetadata: Record<string, CategoryMetadata> = Object.fromEntries(
    [customizeYourInstance].map((category) => {
        const metadata = category as CategoryMetadata;
        return [metadata.label, metadata];
    }),
);

/**
 * Get the description for a category by its slug.
 * Returns a fallback message if no description is defined.
 */
export function getCategoryDescription(categorySlug: string): string {
    const metadata = categoryMetadata[categorySlug];
    if (metadata?.description) {
        return metadata.description;
    }
    // Fallback for categories without descriptions
    const label = metadata?.label || categorySlug.replace(/[-_]/g, " ");
    return `Resources in the ${label} category.`;
}
