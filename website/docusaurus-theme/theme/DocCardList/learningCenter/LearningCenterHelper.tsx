import CategoryNav from "../../../components/LearningCenter/CategoryNav";
import DifficultyFilter from "../../../components/LearningCenter/DifficultyFilter";
import FilterInput from "../../../components/LearningCenter/FilterInput";
import commonStyles from "../../../components/LearningCenter/styling/common.module.css";
import filterStyles from "../../../components/LearningCenter/styling/filters.module.css";
import type { DifficultyLevel, LearningCenterResource } from "../../utils/learningCenter/utils";
import CategoryDescriptions from "./components/CategoryDescriptions";
import NoResults from "./components/NoResults";
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
    /** Initial text filter state, typically from URL query params */
    initialFilter?: string;
    /** Initial category filter state, typically from URL query params */
    initialCategories?: string[];
    /** Initial difficulty filter state, typically from URL query params */
    initialDifficulty?: DifficultyLevel | null;
}

/**
 * LearningCenterHelper provides search and filtering functionality for learning resources.
 * It uses a render prop pattern to allow flexible rendering while managing state and interactions.
 */
export function LearningCenterHelper({
    resources,
    children,
    className,
    initialFilter,
    initialCategories,
    initialDifficulty,
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
    } = useLearningCenterFilter(resources, {
        initialFilter,
        initialCategories,
        initialDifficulty,
    });

    return (
        <div className={clsx(commonStyles.learningCenter, className)}>
            <section className={filterStyles.filterModeSection} aria-label="Browse by filters">
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
            </section>

            <CategoryDescriptions selectedCategories={selectedCategories} />

            <div className={commonStyles.resourceList}>
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
