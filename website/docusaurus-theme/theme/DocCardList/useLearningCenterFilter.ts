import { groupByFirstLetter, type Grouped } from "../../components/LearningCenter/utils";
import {
    applyLearningCenterFilters,
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
    const [filter, setFilterValue] = useState("");
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
        return applyLearningCenterFilters(resources, {
            query: debouncedFilter,
            selectedCategories,
            selectedDifficulty,
            selectedLearningPath,
        });
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

    const setFilter = useCallback((value: string) => {
        if (value.trim()) {
            setSelectedLearningPath(null);
        }
        setFilterValue(value);
    }, []);

    const toggleCategory = useCallback((category: string) => {
        setSelectedLearningPath(null);
        setSelectedCategories((prev) => {
            if (prev.includes(category)) return prev.filter((c) => c !== category);
            return [...prev, category];
        });
    }, []);

    const setDifficulty = useCallback((difficulty: DifficultyLevel | null) => {
        setSelectedLearningPath(null);
        setSelectedDifficulty(difficulty);
    }, []);

    const setLearningPath = useCallback((pathTag: string | null) => {
        setSelectedLearningPath(pathTag);
        if (pathTag !== null) {
            setSelectedCategories([]);
            setSelectedDifficulty(null);
            setFilterValue("");
            setDebouncedFilter("");
        }
    }, []);

    const clearFilter = useCallback(() => setFilterValue(""), []);

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
