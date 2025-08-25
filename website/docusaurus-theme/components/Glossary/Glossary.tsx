import AlphaNav from "./AlphaNav";
import CategorizedTermItem from "./CategorizedTermItem";
import FilterInput from "./FilterInput";
import SectionNav from "./SectionNav";
import SimplifiedTermItem from "./SimplifiedTermItem";
import styles from "./styles.module.css";
import { formatTag, groupByFirstLetter, groupByTag } from "./utils";
import ViewToggle from "./ViewToggle";

import { useHistory, useLocation } from "@docusaurus/router";
import clsx from "clsx";
import React, { useEffect, useMemo, useState } from "react";

export interface GlossaryTerm {
    id: string;
    term: string;
    shortDefinition: string;
    fullDefinition?: string;
    tags?: ReadonlyArray<string>;
    shortHtml?: string;
    fullHtml?: string;
}

export interface GlossaryProps {
    terms: ReadonlyArray<Readonly<GlossaryTerm>>;
    className?: string;
}

export const Glossary: React.FC<GlossaryProps> = ({ terms, className }) => {
    const [expandedTerms, setExpandedTerms] = useState<Record<string, boolean>>({});
    const [filter, setFilter] = useState("");
    const [filteredTerms, setFilteredTerms] = useState<ReadonlyArray<GlossaryTerm>>(terms);
    const [selectedTags, setSelectedTags] = useState<string[]>([]);
    const [isSimplifiedView, setIsSimplifiedView] = useState(false);

    const location = useLocation();
    const history = useHistory();
    // Read selected term from the URL (?term=<id>)
    const selectedTermId = useMemo(() => {
        const sp = new URLSearchParams(location.search);
        return sp.get("term") || "";
    }, [location.search]);

    const toggleTerm = (id: string) => {
        setExpandedTerms((prev) => ({
            ...prev,
            [id]: !prev[id],
        }));
    };

    // Pre-computed groupings for the two view modes
    const termsByTag = React.useMemo(
        () => groupByTag<GlossaryTerm>(filteredTerms),
        [filteredTerms],
    );

    const termsByAlphabet = React.useMemo(
        () => groupByFirstLetter<GlossaryTerm>(filteredTerms),
        [filteredTerms],
    );

    // All tags available across the dataset for the tag filter bar
    const availableTags = React.useMemo(() => {
        const tags = new Set<string>();
        terms.forEach((t) => {
            if (t.tags && t.tags.length) t.tags.forEach((tag) => tags.add(tag));
        });
        return Array.from(tags).sort();
    }, [terms]);

    // Apply text filter (A–Z view) and tag filters (categorized view)
    useEffect(() => {
        let result = terms;

        if (filter && isSimplifiedView) {
            const lowerFilter = filter.toLowerCase();
            result = result.filter(
                (term) =>
                    term.term.toLowerCase().includes(lowerFilter) ||
                    term.shortDefinition.toLowerCase().includes(lowerFilter) ||
                    (term.fullDefinition &&
                        term.fullDefinition.toLowerCase().includes(lowerFilter)),
            );
        }

        if (selectedTags.length > 0 && !isSimplifiedView) {
            result = result.filter((term) =>
                (term.tags || ["General"]).some((t) => selectedTags.includes(t)),
            );
        }

        setFilteredTerms(result);
    }, [filter, selectedTags, terms, isSimplifiedView]);

    // Expand and scroll to a selected term if present in the current filtered set
    useEffect(() => {
        if (!selectedTermId) return;
        // Expand the selected term if it exists in the current filtered set
        const termExists = filteredTerms.some((t) => t.id === selectedTermId);
        if (termExists) {
            setExpandedTerms((prev) => ({ ...prev, [selectedTermId]: true }));
            const el = document.getElementById(selectedTermId);
            if (el) {
                el.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        }
    }, [selectedTermId, filteredTerms]);

    const linkToTerm = (id: string) => {
        const search = new URLSearchParams(location.search);
        search.set("term", id);
        history.replace({ pathname: location.pathname, search: `?${search.toString()}` });
        setExpandedTerms((prev) => ({ ...prev, [id]: true }));
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    const toggleTag = (tag: string) => {
        setSelectedTags((prev) => {
            if (prev.includes(tag)) return prev.filter((s) => s !== tag);
            return [...prev, tag];
        });
    };

    return (
        <div className={clsx(styles.glossary, className)}>
            <ViewToggle
                isSimplifiedView={isSimplifiedView}
                onChange={(v) => {
                    setIsSimplifiedView(v);
                    if (!v) setSelectedTags((prev) => prev);
                }}
            />

            {isSimplifiedView && (
                <>
                    <FilterInput
                        value={filter}
                        onChange={setFilter}
                        onClear={() => setFilter("")}
                    />
                    <AlphaNav letters={termsByAlphabet.map(([letter]) => letter)} />
                </>
            )}

            {!isSimplifiedView && (
                <SectionNav
                    availableTags={availableTags}
                    selectedTags={selectedTags}
                    onToggleTag={toggleTag}
                    onClear={() => setSelectedTags([])}
                />
            )}

            <div className={styles.termList}>
                {filteredTerms.length > 0 ? (
                    isSimplifiedView ? (
                        termsByAlphabet.map(([letter, letterTerms]) => (
                            <div
                                key={letter}
                                className={styles.simplifiedSection}
                                id={`letter-${letter}`}
                            >
                                <h2 className={styles.sectionTitle}>{letter}</h2>
                                <div className={styles.simplifiedTerms}>
                                    {letterTerms.map((term) => (
                                        <SimplifiedTermItem
                                            key={term.id}
                                            term={term}
                                            expanded={Boolean(expandedTerms[term.id])}
                                            onToggle={() => toggleTerm(term.id)}
                                            onLinkClick={() => linkToTerm(term.id)}
                                            linkHref={`${location.pathname}?term=${encodeURIComponent(term.id)}`}
                                        />
                                    ))}
                                </div>
                            </div>
                        ))
                    ) : (
                        termsByTag.map(([tag, tagTerms]) => (
                            <div key={tag} className={styles.section}>
                                <h2 className={styles.sectionTitle}>{formatTag(tag)}</h2>
                                <div className={styles.sectionTerms}>
                                    {tagTerms.map((term) => (
                                        <CategorizedTermItem
                                            key={term.id}
                                            term={term}
                                            expanded={Boolean(expandedTerms[term.id])}
                                            onToggle={() => toggleTerm(term.id)}
                                            onLinkClick={() => linkToTerm(term.id)}
                                            linkHref={`${location.pathname}?term=${encodeURIComponent(term.id)}`}
                                        />
                                    ))}
                                </div>
                            </div>
                        ))
                    )
                ) : (
                    <div className={styles.noResults}>
                        <p>No terms match your filter criteria.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Glossary;
