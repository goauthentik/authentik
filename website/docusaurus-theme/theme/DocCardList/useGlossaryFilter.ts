import { groupByFirstLetter, type Grouped } from "../../components/Glossary/utils";
import { extractAvailableTags, type GlossaryHelperTerm } from "../utils/glossaryUtils";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const DEBOUNCE_MS = 150;

export type ViewMode = "categorized" | "alphabetical";

export interface UseGlossaryFilterResult {
    /** Current text filter value (immediate, for input field) */
    filter: string;
    /** Debounced filter value (for filtering and highlighting) */
    debouncedFilter: string;
    /** Update the text filter */
    setFilter: (value: string) => void;
    /** Clear the text filter */
    clearFilter: () => void;
    /** Currently selected tags for categorized view */
    selectedTags: string[];
    /** Toggle a tag selection */
    toggleTag: (tag: string) => void;
    /** Whether simplified (alphabetical) view is active */
    simplifiedView: boolean;
    /** Handle view toggle between categorized and alphabetical */
    handleViewToggle: (simplified: boolean) => void;
    /** Current view mode */
    viewMode: ViewMode;
    /** Terms after applying all filters */
    filteredTerms: GlossaryHelperTerm[];
    /** Terms grouped by first letter (for alphabetical view) */
    termsByAlphabet: Grouped<GlossaryHelperTerm>;
    /** All available tags extracted from terms */
    availableTags: string[];
}

/**
 * Custom hook that manages glossary filtering state and logic.
 * Handles text search, tag filtering, and view mode switching.
 */
export function useGlossaryFilter(terms: GlossaryHelperTerm[]): UseGlossaryFilterResult {
    const [filter, setFilter] = useState("");
    const [debouncedFilter, setDebouncedFilter] = useState("");
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const [simplifiedView, setSimplifiedView] = useState(true);
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

    // Apply filters based on current view mode and user selections
    const filteredTerms = useMemo(() => {
        let result = terms;

        // Text search filter (uses debounced value)
        if (debouncedFilter) {
            const lowerFilter = debouncedFilter.toLowerCase();
            result = result.filter(
                (term) =>
                    term.term.toLowerCase().includes(lowerFilter) ||
                    term.shortDefinition.toLowerCase().includes(lowerFilter) ||
                    (term.fullDefinition &&
                        term.fullDefinition.toLowerCase().includes(lowerFilter)),
            );
        }

        // Tag filter - only active in categorized view
        if (selectedTags.length > 0 && !simplifiedView) {
            result = result.filter((term) =>
                (term.tags || ["General"]).some((t) => selectedTags.includes(t)),
            );
        }

        return result;
    }, [debouncedFilter, selectedTags, terms, simplifiedView]);

    // Pre-computed groupings
    const termsByAlphabet = useMemo(
        () => groupByFirstLetter<GlossaryHelperTerm>(filteredTerms),
        [filteredTerms],
    );

    // Extract all unique tags from terms for the tag filter bar
    const availableTags = useMemo(() => extractAvailableTags(terms), [terms]);

    const toggleTag = useCallback((tag: string) => {
        setSelectedTags((prev) => {
            if (prev.includes(tag)) return prev.filter((s) => s !== tag);
            return [...prev, tag];
        });
    }, []);

    const clearFilter = useCallback(() => setFilter(""), []);

    const handleViewToggle = useCallback((simplified: boolean) => {
        setSimplifiedView(simplified);
        // Clear tag filters when switching to alphabetical view
        if (simplified) setSelectedTags([]);
    }, []);

    const viewMode: ViewMode = simplifiedView ? "alphabetical" : "categorized";

    return {
        filter,
        debouncedFilter,
        setFilter,
        clearFilter,
        selectedTags,
        toggleTag,
        simplifiedView,
        handleViewToggle,
        viewMode,
        filteredTerms,
        termsByAlphabet,
        availableTags,
    };
}
