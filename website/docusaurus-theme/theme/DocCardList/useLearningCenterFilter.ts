import { groupByFirstLetter, type Grouped } from "../../components/LearningCenter/utils";
import {
    type DifficultyLevel,
    extractAvailableCategories,
    extractAvailableDifficulties,
    type LearningCenterResource,
} from "../utils/learningCenterUtils";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const DEBOUNCE_MS = 150;

export interface UseLearningCenterFilterResult {
    /** Current text filter value (immediate, for input field) */
    filter: string;
    /** Debounced filter value (for filtering and highlighting) */
    debouncedFilter: string;
    /** Update the text filter */
    setFilter: (value: string) => void;
    /** Clear the text filter */
    clearFilter: () => void;
    /** Currently selected categories */
    selectedCategories: string[];
    /** Toggle a category selection */
    toggleCategory: (category: string) => void;
    /** Currently selected difficulty */
    selectedDifficulty: DifficultyLevel | null;
    /** Set difficulty filter */
    setDifficulty: (difficulty: DifficultyLevel | null) => void;
    /** Currently selected learning path tag */
    selectedLearningPath: string | null;
    /** Set learning path filter */
    setLearningPath: (pathTag: string | null) => void;
    /** Resources after applying all filters */
    filteredResources: LearningCenterResource[];
    /** Resources grouped by first letter (for alphabetical navigation) */
    resourcesByAlphabet: Grouped<LearningCenterResource>;
    /** All available categories extracted from resources */
    availableCategories: string[];
    /** All available difficulty levels extracted from resources */
    availableDifficulties: DifficultyLevel[];
}

/**
 * Custom hook that manages learning center filtering state and logic.
 * Handles text search, category filtering, tag filtering, and difficulty filtering.
 */
export function useLearningCenterFilter(
    resources: LearningCenterResource[],
): UseLearningCenterFilterResult {
    const [filter, setFilter] = useState("");
    const [debouncedFilter, setDebouncedFilter] = useState("");
    const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
    const [selectedDifficulty, setSelectedDifficulty] = useState<DifficultyLevel | null>(null);
    const [selectedLearningPath, setSelectedLearningPath] = useState<string | null>(null);
    const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

    // Debounce the filter value for performance
    useEffect(() => {
        debounceRef.current = setTimeout(() => {
            setDebouncedFilter(filter);
        }, DEBOUNCE_MS);

        return () => {
            if (debounceRef.current) {
                clearTimeout(debounceRef.current);
            }
        };
    }, [filter]);

    // Apply filters based on current selections
    const filteredResources = useMemo(() => {
        let result = resources;

        // Text search filter (uses debounced value)
        if (debouncedFilter) {
            const lowerFilter = debouncedFilter.toLowerCase();
            result = result.filter(
                (resource) =>
                    resource.resourceName.toLowerCase().includes(lowerFilter) ||
                    resource.shortDescription.toLowerCase().includes(lowerFilter) ||
                    (resource.longDescription &&
                        resource.longDescription.toLowerCase().includes(lowerFilter)) ||
                    resource.category.toLowerCase().includes(lowerFilter),
            );
        }

        // Category filter
        if (selectedCategories.length > 0) {
            result = result.filter((resource) => selectedCategories.includes(resource.category));
        }

        // Difficulty filter
        if (selectedDifficulty) {
            result = result.filter((resource) => resource.difficulty === selectedDifficulty);
        }

        // Learning path filter (filters by learningPaths field)
        if (selectedLearningPath) {
            result = result.filter((resource) =>
                resource.learningPaths.includes(selectedLearningPath),
            );
        }

        return result;
    }, [debouncedFilter, selectedCategories, selectedDifficulty, selectedLearningPath, resources]);

    // Pre-computed grouping for alphabetical navigation
    const resourcesByAlphabet = useMemo(
        () => groupByFirstLetter(filteredResources),
        [filteredResources],
    );

    // Extract all unique values from resources
    const availableCategories = useMemo(() => extractAvailableCategories(resources), [resources]);
    const availableDifficulties = useMemo(
        () => extractAvailableDifficulties(resources),
        [resources],
    );

    const toggleCategory = useCallback((category: string) => {
        setSelectedCategories((prev) => {
            if (prev.includes(category)) return prev.filter((c) => c !== category);
            return [...prev, category];
        });
    }, []);

    const setDifficulty = useCallback((difficulty: DifficultyLevel | null) => {
        setSelectedDifficulty(difficulty);
    }, []);

    const setLearningPath = useCallback((pathTag: string | null) => {
        setSelectedLearningPath(pathTag);
    }, []);

    const clearFilter = useCallback(() => setFilter(""), []);

    return {
        filter,
        debouncedFilter,
        setFilter,
        clearFilter,
        selectedCategories,
        toggleCategory,
        selectedDifficulty,
        setDifficulty,
        selectedLearningPath,
        setLearningPath,
        filteredResources,
        resourcesByAlphabet,
        availableCategories,
        availableDifficulties,
    };
}
