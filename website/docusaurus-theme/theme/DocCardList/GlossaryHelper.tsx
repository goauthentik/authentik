import AlphaNav from "../../components/Glossary/AlphaNav";
import FilterInput from "../../components/Glossary/FilterInput";
import SectionNav from "../../components/Glossary/SectionNav";
import styles from "../../components/Glossary/styles.module.css";
import ViewToggle from "../../components/Glossary/ViewToggle";
import type { GlossaryHelperTerm } from "../utils/glossaryUtils";
import { useGlossaryFilter, type ViewMode } from "./useGlossaryFilter";

import clsx from "clsx";
import type { ReactNode } from "react";

/**
 * Props for GlossaryHelper component
 */
export interface GlossaryHelperProps {
    /** Array of glossary terms to display and filter */
    terms: GlossaryHelperTerm[];
    /** Render prop that receives filtered terms, current view mode, and search filter */
    children: (
        filteredTerms: GlossaryHelperTerm[],
        viewMode: ViewMode,
        searchFilter: string,
    ) => ReactNode;
    /** Optional CSS class name for styling */
    className?: string;
}

/**
 * Displayed when no terms match the current filter criteria.
 */
function NoResults() {
    return (
        <div className={styles.noResults}>
            <p>No terms match your filter criteria.</p>
        </div>
    );
}

/**
 * GlossaryHelper provides search, filtering, and view toggle functionality for glossary terms.
 * It uses a render prop pattern to allow flexible rendering while managing state and interactions.
 */
export function GlossaryHelper({ terms, children, className }: GlossaryHelperProps): ReactNode {
    const {
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
    } = useGlossaryFilter(terms);

    return (
        <div className={clsx(styles.glossary, className)}>
            <ViewToggle isSimplifiedView={simplifiedView} onChange={handleViewToggle} />

            <FilterInput value={filter} onChange={setFilter} onClear={clearFilter} />

            {simplifiedView ? (
                <AlphaNav letters={termsByAlphabet.map(([letter]) => letter)} />
            ) : (
                <SectionNav
                    availableTags={availableTags}
                    selectedTags={selectedTags}
                    onToggleTag={toggleTag}
                />
            )}

            <div className={styles.termList}>
                {filteredTerms.length > 0 ? (
                    children(filteredTerms, viewMode, debouncedFilter)
                ) : (
                    <NoResults />
                )}
            </div>
        </div>
    );
}

export default GlossaryHelper;
