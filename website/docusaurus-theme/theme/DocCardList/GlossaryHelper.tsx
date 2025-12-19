import AlphaNav from "../../components/Glossary/AlphaNav";
import FilterInput from "../../components/Glossary/FilterInput";
import SectionNav from "../../components/Glossary/SectionNav";
import styles from "../../components/Glossary/styles.module.css";
import { groupByFirstLetter, groupByTag } from "../../components/Glossary/utils";
import ViewToggle from "../../components/Glossary/ViewToggle";
import { extractAvailableTags, type GlossaryHelperTerm } from "../utils/glossaryUtils";

import clsx from "clsx";
import React, { useCallback, useState } from "react";

/**
 * Props for GlossaryHelper component
 */
export interface GlossaryHelperProps {
    /** Array of glossary terms to display and filter */
    terms: GlossaryHelperTerm[];
    /** Render prop that receives filtered terms and current view mode */
    children: (
        filteredTerms: GlossaryHelperTerm[],
        viewMode: "categorized" | "alphabetical",
    ) => React.ReactNode;
    /** Optional CSS class name for styling */
    className?: string;
}

/**
 * GlossaryHelper provides search, filtering, and view toggle functionality for glossary terms.
 * It uses a render prop pattern to allow flexible rendering while managing state and interactions.
 */
export const GlossaryHelper: React.FC<GlossaryHelperProps> = ({ terms, children, className }) => {
    const [filter, setFilter] = useState(""); // Text search filter for alphabetical view
    const [selectedTags, setSelectedTags] = useState<string[]>([]); // Selected tag filters for categorized view
    const [isSimplifiedView, setIsSimplifiedView] = useState(true); // false = categorized, true = alphabetical

    // Apply filters based on current view mode and user selections using useMemo instead of useEffect
    const filteredTerms = React.useMemo(() => {
        let result = terms;

        // Text search filter
        if (filter) {
            const lowerFilter = filter.toLowerCase();
            result = result.filter(
                (term) =>
                    term.term.toLowerCase().includes(lowerFilter) ||
                    term.shortDefinition.toLowerCase().includes(lowerFilter) ||
                    (term.fullDefinition &&
                        term.fullDefinition.toLowerCase().includes(lowerFilter)),
            );
        }

        // Tag filter - only active in categorized view
        if (selectedTags.length > 0 && !isSimplifiedView) {
            result = result.filter((term) =>
                (term.tags || ["General"]).some((t) => selectedTags.includes(t)),
            );
        }

        return result;
    }, [filter, selectedTags, terms, isSimplifiedView]);

    // Pre-computed groupings for the two view modes
    const _termsByTag = React.useMemo(
        () => groupByTag<GlossaryHelperTerm>(filteredTerms),
        [filteredTerms],
    );

    const termsByAlphabet = React.useMemo(
        () => groupByFirstLetter<GlossaryHelperTerm>(filteredTerms),
        [filteredTerms],
    );

    // Extract all unique tags from terms for the tag filter bar
    const availableTags = React.useMemo(() => extractAvailableTags(terms), [terms]);

    /**
     * Toggles tag selection for filtering in categorized view
     */
    const toggleTag = useCallback((tag: string) => {
        setSelectedTags((prev) => {
            if (prev.includes(tag)) return prev.filter((s) => s !== tag);
            return [...prev, tag];
        });
    }, []);

    /**
     * Clears text filter
     */
    const clearFilter = useCallback(() => setFilter(""), []);

    /**
     * Handles view toggle change
     */
    const handleViewToggle = useCallback((v: boolean) => {
        setIsSimplifiedView(v);
        // Clear tag filters when switching to alphabetical view
        if (v) setSelectedTags([]);
    }, []);

    return (
        <div className={clsx(styles.glossary, className)}>
            {/* View mode toggle: Tags (by tags) vs Alphabetical (A-Z) */}
            <ViewToggle isSimplifiedView={isSimplifiedView} onChange={handleViewToggle} />

            {/* Search input */}
            <FilterInput value={filter} onChange={setFilter} onClear={clearFilter} />

            {/* Alphabetical view controls */}
            {isSimplifiedView ? (
                <AlphaNav letters={termsByAlphabet.map(([letter]) => letter)} />
            ) : null}

            {/* Tags view controls */}
            {!isSimplifiedView ? (
                <SectionNav
                    availableTags={availableTags}
                    selectedTags={selectedTags}
                    onToggleTag={toggleTag}
                />
            ) : null}

            {/* Render area - delegates to children via render prop pattern */}
            <div className={styles.termList}>
                {filteredTerms.length > 0 ? (
                    children(filteredTerms, isSimplifiedView ? "alphabetical" : "categorized")
                ) : (
                    <div className={styles.noResults}>
                        <p>No terms match your filter criteria.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default GlossaryHelper;
