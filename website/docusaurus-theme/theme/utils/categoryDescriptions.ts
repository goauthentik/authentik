/**
 * Category descriptions loaded from _category_.json files.
 * Import category metadata and export descriptions for use in components.
 */

import categoryA from "../../../docs/core/learning-center/category-a/_category_.json";
import categoryB from "../../../docs/core/learning-center/category-b/_category_.json";
import categoryC from "../../../docs/core/learning-center/category-c/_category_.json";

export interface CategoryMetadata {
    label: string;
    position: number;
    description?: string;
}

/**
 * Map of category names to their metadata from _category_.json files.
 * Add new categories here as they are created.
 */
const categoryMetadata: Record<string, CategoryMetadata> = {
    "Category A": categoryA as CategoryMetadata,
    "Category B": categoryB as CategoryMetadata,
    "Category C": categoryC as CategoryMetadata,
};

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
