import { groupByFirstLetter, type Grouped } from "../../components/LearningCenter/utils";
import {
    type DifficultyLevel,
    extractAvailableCategories,
    extractAvailableDifficulties,
    extractAvailableTags,
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
    /** Currently selected tags */
    selectedTags: string[];
    /** Toggle a tag selection */
    toggleTag: (tag: string) => void;
    /** Currently selected difficulty */
    selectedDifficulty: DifficultyLevel | null;
    /** Set difficulty filter */
    setDifficulty: (difficulty: DifficultyLevel | null) => void;
    /** Resources after applying all filters */
    filteredResources: LearningCenterResource[];
    /** Resources grouped by first letter (for alphabetical navigation) */
    resourcesByAlphabet: Grouped<LearningCenterResource>;
    /** All available categories extracted from resources */
    availableCategories: string[];
    /** All available tags extracted from resources */
    availableTags: string[];
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
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const [selectedDifficulty, setSelectedDifficulty] = useState<DifficultyLevel | null>(null);
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
                    resource.category.toLowerCase().includes(lowerFilter) ||
                    resource.tags.some((tag) => tag.toLowerCase().includes(lowerFilter)),
            );
        }

        // Category filter
        if (selectedCategories.length > 0) {
            result = result.filter((resource) => selectedCategories.includes(resource.category));
        }

        // Tag filter
        if (selectedTags.length > 0) {
            result = result.filter((resource) =>
                resource.tags.some((tag) => selectedTags.includes(tag)),
            );
        }

        // Difficulty filter
        if (selectedDifficulty) {
            result = result.filter((resource) => resource.difficulty === selectedDifficulty);
        }

        return result;
    }, [debouncedFilter, selectedCategories, selectedTags, selectedDifficulty, resources]);

    // Pre-computed grouping for alphabetical navigation
    const resourcesByAlphabet = useMemo(
        () => groupByFirstLetter(filteredResources),
        [filteredResources],
    );

    // Extract all unique values from resources
    const availableCategories = useMemo(() => extractAvailableCategories(resources), [resources]);
    const availableTags = useMemo(() => extractAvailableTags(resources), [resources]);
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

    const toggleTag = useCallback((tag: string) => {
        setSelectedTags((prev) => {
            if (prev.includes(tag)) return prev.filter((t) => t !== tag);
            return [...prev, tag];
        });
    }, []);

    const setDifficulty = useCallback((difficulty: DifficultyLevel | null) => {
        setSelectedDifficulty(difficulty);
    }, []);

    const clearFilter = useCallback(() => setFilter(""), []);

    return {
        filter,
        debouncedFilter,
        setFilter,
        clearFilter,
        selectedCategories,
        toggleCategory,
        selectedTags,
        toggleTag,
        selectedDifficulty,
        setDifficulty,
        filteredResources,
        resourcesByAlphabet,
        availableCategories,
        availableTags,
        availableDifficulties,
    };
}
