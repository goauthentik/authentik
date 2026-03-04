import {
    applyLearningCenterFilters,
    DIFFICULTY_LEVELS,
    type DifficultyLevel,
    extractAvailableCategories,
    extractAvailableDifficulties,
    type LearningCenterResource,
} from "../../utils/learningCenter/utils";

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
    /** Resources after applying all filters */
    filteredResources: LearningCenterResource[];
    /** All available categories extracted from resources */
    availableCategories: string[];
    /** All available difficulty levels extracted from resources */
    availableDifficulties: DifficultyLevel[];
}

export interface UseLearningCenterFilterOptions {
    initialFilter?: string;
    initialCategories?: string[];
    initialDifficulty?: DifficultyLevel | null;
}

function sanitizeInitialCategories(
    resources: LearningCenterResource[],
    initialCategories: string[] | undefined,
): string[] {
    if (!initialCategories || initialCategories.length === 0) {
        return [];
    }

    const availableCategories = new Set(resources.map((resource) => resource.category));
    return Array.from(
        new Set(initialCategories.filter((category) => availableCategories.has(category))),
    );
}

function sanitizeInitialDifficulty(
    initialDifficulty: DifficultyLevel | null | undefined,
): DifficultyLevel | null {
    if (!initialDifficulty) {
        return null;
    }
    return DIFFICULTY_LEVELS.includes(initialDifficulty) ? initialDifficulty : null;
}

/**
 * Custom hook that manages learning center filtering state and logic.
 * Handles text search, category filtering, tag filtering, and difficulty filtering.
 */
export function useLearningCenterFilter(
    resources: LearningCenterResource[],
    options: UseLearningCenterFilterOptions = {},
): UseLearningCenterFilterResult {
    const [filter, setFilterValue] = useState(() => options.initialFilter?.trim() ?? "");
    const [debouncedFilter, setDebouncedFilter] = useState(
        () => options.initialFilter?.trim() ?? "",
    );
    const [selectedCategories, setSelectedCategories] = useState<string[]>(() =>
        sanitizeInitialCategories(resources, options.initialCategories),
    );
    const [selectedDifficulty, setSelectedDifficulty] = useState<DifficultyLevel | null>(() =>
        sanitizeInitialDifficulty(options.initialDifficulty),
    );
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
        });
    }, [debouncedFilter, selectedCategories, selectedDifficulty, resources]);

    // Extract all unique values from resources
    const availableCategories = useMemo(() => extractAvailableCategories(resources), [resources]);
    const availableDifficulties = useMemo(
        () => extractAvailableDifficulties(resources),
        [resources],
    );

    const setFilter = useCallback((value: string) => {
        setFilterValue(value);
    }, []);

    const toggleCategory = useCallback((category: string) => {
        setSelectedCategories((prev) => {
            if (prev.includes(category)) return prev.filter((c) => c !== category);
            return [...prev, category];
        });
    }, []);

    const setDifficulty = useCallback((difficulty: DifficultyLevel | null) => {
        setSelectedDifficulty(difficulty);
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
        filteredResources,
        availableCategories,
        availableDifficulties,
    };
}
