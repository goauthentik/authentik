import CategoryNav from "../../components/LearningCenter/CategoryNav";
import DifficultyFilter from "../../components/LearningCenter/DifficultyFilter";
import FilterInput from "../../components/LearningCenter/FilterInput";
import styles from "../../components/LearningCenter/styles.module.css";
import { getCategoryDescription } from "../utils/categoryDescriptions";
import type { LearningCenterResource } from "../utils/learningCenterUtils";
import { useLearningCenterFilter } from "./useLearningCenterFilter";

import clsx from "clsx";
import type { ReactNode } from "react";

/**
 * Props for LearningCenterHelper component
 */
export interface LearningCenterHelperProps {
    /** Array of learning center resources to display and filter */
    resources: LearningCenterResource[];
    /** Render prop that receives filtered resources and search filter */
    children: (filteredResources: LearningCenterResource[], searchFilter: string) => ReactNode;
    /** Optional CSS class name for styling */
    className?: string;
}

/**
 * Displayed when no resources match the current filter criteria.
 */
function NoResults() {
    return (
        <div className={styles.noResults}>
            <p>No resources match your filter criteria.</p>
        </div>
    );
}

/**
 * Displays descriptions for selected categories.
 */
function CategoryDescriptions({ selectedCategories }: { selectedCategories: string[] }) {
    if (selectedCategories.length === 0) return null;

    return (
        <div className={styles.categoryDescriptions}>
            {selectedCategories.map((category) => (
                <p key={category} className={styles.categoryDescriptionText}>
                    <strong>{category}</strong>: {getCategoryDescription(category)}
                </p>
            ))}
        </div>
    );
}

/**
 * LearningCenterHelper provides search and filtering functionality for learning resources.
 * It uses a render prop pattern to allow flexible rendering while managing state and interactions.
 */
export function LearningCenterHelper({
    resources,
    children,
    className,
}: LearningCenterHelperProps): ReactNode {
    const {
        filter,
        debouncedFilter,
        setFilter,
        clearFilter,
        selectedCategories,
        toggleCategory,
        selectedDifficulty,
        setDifficulty,
        filteredResources,
        availableCategories,
        availableDifficulties,
    } = useLearningCenterFilter(resources);

    return (
        <div className={clsx(styles.learningCenter, className)}>
            <FilterInput value={filter} onChange={setFilter} onClear={clearFilter} />

            {availableCategories.length > 1 && (
                <CategoryNav
                    availableCategories={availableCategories}
                    selectedCategories={selectedCategories}
                    onToggleCategory={toggleCategory}
                />
            )}

            {availableDifficulties.length > 1 && (
                <DifficultyFilter
                    availableDifficulties={availableDifficulties}
                    selectedDifficulty={selectedDifficulty}
                    onSelectDifficulty={setDifficulty}
                />
            )}

            <CategoryDescriptions selectedCategories={selectedCategories} />

            <div className={styles.resourceList}>
                {filteredResources.length > 0 ? (
                    children(filteredResources, debouncedFilter)
                ) : (
                    <NoResults />
                )}
            </div>
        </div>
    );
}

export default LearningCenterHelper;
