import glossaryStyles from "../../components/Glossary/styles.module.css";
import { formatTag, groupByFirstLetter, groupByTag } from "../../components/Glossary/utils";
import {
    type GlossaryHelperTerm,
    safeBooleanExtract,
    safeStringArrayExtract,
    safeStringExtract,
} from "../utils/glossaryUtils";
import ErrorBoundary from "./ErrorBoundary";
import GlossaryHelper from "./GlossaryHelper";
import sharedStyles from "./shared.module.css";
import styles from "./styles.module.css";

import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";
import clsx from "clsx";
import React, { ReactNode, useCallback, useMemo } from "react";

type SidebarDocLike = Extract<PropSidebarItem, { type: "link" }>;

interface GlossaryDocCardListProps {
    glossaryPool: SidebarDocLike[];
    className?: string;
}

/**
 * Cache structure for glossary term data - key is guaranteed to be a string docId
 */
interface TermCache {
    [docId: string]: {
        termName: string;
        tags: string[];
        shortDescription: string;
        longDescription: string;
        authentikSpecific: boolean;
    };
}

/**
 * Safely extracts label from sidebar item
 */
function getLabelFromItem(item: PropSidebarItem): string {
    if ("label" in item && typeof item.label === "string") return item.label;
    return "";
}

/**
 * Splits text into paragraphs for better formatting in long descriptions
 */
function splitParagraphs(text: string): string[] {
    return text
        .split(/\n{2,}/)
        .map((part) => part.trim())
        .filter((part) => part.length > 0);
}

/**
 * Highlights matching search terms in text
 */
function highlightText(
    text: string,
    searchFilter: string,
    keyPrefix: string,
): (string | React.ReactElement)[] {
    if (!searchFilter) return [text];

    const escaped = searchFilter.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`(${escaped})`, "gi");
    const matches = text.split(regex);

    return matches.map((part, i) => {
        if (part.toLowerCase() === searchFilter.toLowerCase()) {
            return (
                <mark key={`${keyPrefix}-${i}`} className={sharedStyles.searchHighlight}>
                    {part}
                </mark>
            );
        }
        return part;
    });
}

/**
 * Converts backticks to code elements and highlights search matches
 */
function renderMarkdown(
    text: string,
    searchFilter: string = "",
    keyPrefix: string = "md",
): (string | React.ReactElement)[] {
    const parts: (string | React.ReactElement)[] = [];
    const regex = /`([^`]+)`/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
        // Add text before the match (with highlighting)
        if (match.index > lastIndex) {
            const textBefore = text.substring(lastIndex, match.index);
            parts.push(...highlightText(textBefore, searchFilter, `${keyPrefix}-${lastIndex}`));
        }
        // Add the code element (with highlighting inside)
        const codeContent = highlightText(
            match[1] ?? "",
            searchFilter,
            `${keyPrefix}-code-${match.index}`,
        );
        parts.push(<code key={`${keyPrefix}-${match.index}`}>{codeContent}</code>);
        lastIndex = regex.lastIndex;
    }

    // Add remaining text (with highlighting)
    if (lastIndex < text.length) {
        const remaining = text.substring(lastIndex);
        parts.push(...highlightText(remaining, searchFilter, `${keyPrefix}-${lastIndex}`));
    }

    return parts.length > 0 ? parts : highlightText(text, searchFilter, keyPrefix);
}

/**
 * Renders a single glossary term as a card with title, short description, and long description.
 */
function GlossaryTermCard({
    item,
    termCache,
    searchFilter = "",
}: {
    item: SidebarDocLike;
    termCache: TermCache;
    searchFilter?: string;
}) {
    // Check if search matches ONLY in long description (not visible in title/short)
    // Only auto-expand if the match wouldn't be visible without expanding
    const cachedData = item.docId ? termCache[item.docId] : null;
    const shouldAutoExpand = React.useMemo(() => {
        if (!searchFilter) return false;
        const lowerFilter = searchFilter.toLowerCase();
        const matchesTitle = cachedData?.termName?.toLowerCase().includes(lowerFilter);
        const matchesShort = cachedData?.shortDescription?.toLowerCase().includes(lowerFilter);
        const matchesLong = cachedData?.longDescription?.toLowerCase().includes(lowerFilter);
        return matchesLong && !matchesTitle && !matchesShort;
    }, [searchFilter, cachedData]);

    const [isExpanded, setIsExpanded] = React.useState(false);
    const userToggledRef = React.useRef(false);

    // Auto-expand only when match is exclusively in long description (not visible otherwise)
    // Once user manually toggles, never auto-control this term again
    React.useEffect(() => {
        if (userToggledRef.current) {
            return;
        }
        if (shouldAutoExpand) {
            setIsExpanded(true);
        } else if (!searchFilter) {
            setIsExpanded(false);
        }
    }, [shouldAutoExpand, searchFilter]);

    // Ensure item has a valid docId and cached data before rendering
    if (!item.docId) {
        console.error(`DocCardList: glossary item missing docId:`, item);
        return null;
    }

    if (!cachedData) {
        console.error(`DocCardList: no cached data found for glossary term '${item.docId}'.`);
        return null;
    }

    const { termName, tags, shortDescription, longDescription, authentikSpecific } = cachedData;
    const longParagraphs = splitParagraphs(longDescription);
    const hasLongDescription = longParagraphs.length > 0;

    // Create anchor ID from term name
    const anchorId = termName
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, "") // Remove special characters except spaces and hyphens
        .replace(/\s+/g, "-") // Replace spaces with hyphens
        .replace(/-+/g, "-") // Replace multiple hyphens with single hyphen
        .replace(/^-|-$/g, ""); // Remove leading/trailing hyphens

    const handleCopyLink = () => {
        // We can't use anchors since Docusaurus will fail to build due to anchors being generated dynamically
        const url = `${window.location.origin}${window.location.pathname}?${anchorId}`;
        navigator.clipboard.writeText(url);
    };

    return (
        <article
            id={anchorId}
            className={clsx(styles.docCardListItem, sharedStyles.cardContainer, "col col--12")}
            data-tags={tags.join(",")}
        >
            <div className={clsx("card margin-bottom--md", sharedStyles.compactCard)}>
                <div className="card__header">
                    <h3 className="margin-vert--none" aria-label={termName || "Glossary term"}>
                        {highlightText(termName || "Glossary term", searchFilter, "term")}
                        {authentikSpecific ? (
                            <span
                                className={sharedStyles.authentikBadge}
                                title="authentik-specific term"
                            >
                                authentik specific
                            </span>
                        ) : null}
                        <a
                            href={`?${anchorId}`}
                            className={sharedStyles.anchorLink}
                            aria-label={`Copy link to ${termName}`}
                            onClick={handleCopyLink}
                            title="Copy link to this term"
                        >
                            <svg
                                width="16"
                                height="16"
                                viewBox="0 0 16 16"
                                fill="currentColor"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <path d="M7.775 3.275a.75.75 0 001.06 1.06l1.25-1.25a2 2 0 112.83 2.83l-2.5 2.5a2 2 0 01-2.83 0 .75.75 0 00-1.06 1.06 3.5 3.5 0 004.95 0l2.5-2.5a3.5 3.5 0 00-4.95-4.95l-1.25 1.25zm-4.69 9.64a2 2 0 010-2.83l2.5-2.5a2 2 0 012.83 0 .75.75 0 001.06-1.06 3.5 3.5 0 00-4.95 0l-2.5 2.5a3.5 3.5 0 004.95 4.95l1.25-1.25a.75.75 0 00-1.06-1.06l-1.25 1.25a2 2 0 01-2.83 0z" />
                            </svg>
                        </a>
                    </h3>
                </div>
                <div className="card__body">
                    <div
                        className={clsx(
                            sharedStyles.glossaryShort,
                            !shortDescription && sharedStyles.glossaryShortMissing,
                        )}
                    >
                        {shortDescription
                            ? renderMarkdown(shortDescription, searchFilter, "short")
                            : "Short description not provided."}
                    </div>

                    {hasLongDescription ? (
                        <>
                            <button
                                className={sharedStyles.expandButton}
                                onClick={() => {
                                    setIsExpanded(!isExpanded);
                                    userToggledRef.current = true;
                                }}
                                aria-expanded={isExpanded}
                                aria-controls={`${anchorId}-details`}
                            >
                                {isExpanded ? "▼ Hide details" : "▶ Show details"}
                            </button>
                            {isExpanded ? (
                                <div
                                    id={`${anchorId}-details`}
                                    className={sharedStyles.glossaryLong}
                                >
                                    {longParagraphs.map((paragraph, index) => (
                                        <p key={index}>
                                            {renderMarkdown(
                                                paragraph,
                                                searchFilter,
                                                `long-${index}`,
                                            )}
                                        </p>
                                    ))}
                                </div>
                            ) : null}
                        </>
                    ) : null}
                </div>
            </div>
        </article>
    );
}

/**
 * Component for rendering glossary terms with search, filtering, and view modes.
 */
export default function GlossaryDocCardList({
    glossaryPool,
    className,
}: GlossaryDocCardListProps): ReactNode {
    // Handle query parameter links on mount and ensure scroll to target
    React.useEffect(() => {
        let timeoutId: ReturnType<typeof setTimeout> | undefined;

        const queryString = window.location.search;
        if (queryString && queryString.length > 1) {
            const termId = queryString.substring(1); // Remove the '?'
            const element = document.getElementById(termId);

            if (element) {
                element.scrollIntoView({ behavior: "smooth", block: "start" });
            } else {
                // If not found, try after a delay to allow DOM to render
                timeoutId = setTimeout(() => {
                    document.getElementById(termId)?.scrollIntoView({
                        behavior: "smooth",
                        block: "start",
                    });
                }, 100);
            }
        }

        return () => {
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, []);

    // Build term cache to avoid repeated useDocById calls with error handling
    const termCache = useMemo<TermCache>(() => {
        const cache: TermCache = {};

        // Filter items to ensure docId is defined, then process them
        glossaryPool
            .filter((item): item is SidebarDocLike & { docId: string } => Boolean(item.docId))
            .forEach((item) => {
                const sidebarProps = item.customProps ?? {};
                const fallbackLabel = getLabelFromItem(item);

                cache[item.docId] = {
                    termName:
                        safeStringExtract(sidebarProps.termName) ||
                        fallbackLabel ||
                        item.docId ||
                        "Glossary term",
                    tags: safeStringArrayExtract(sidebarProps.tags),
                    shortDescription: safeStringExtract(sidebarProps.shortDescription),
                    longDescription: safeStringExtract(sidebarProps.longDescription),
                    authentikSpecific: safeBooleanExtract(sidebarProps.authentikSpecific),
                };
            });

        return cache;
    }, [glossaryPool]);

    // O(1) lookup map for sidebar items by docId
    const sidebarItemMap = useMemo(
        () => new Map(glossaryPool.map((item) => [item.docId, item])),
        [glossaryPool],
    );

    // Transform cached data to standardized GlossaryHelperTerm format
    const glossaryTerms = useMemo<GlossaryHelperTerm[]>(() => {
        return glossaryPool
            .filter((item): item is SidebarDocLike & { docId: string } => Boolean(item.docId))
            .map((item) => {
                const cached = termCache[item.docId];
                if (!cached) {
                    console.warn(`No cached data for term ${item.docId}, skipping`);
                    return null;
                }
                return {
                    id: item.docId,
                    term: cached.termName,
                    shortDefinition: cached.shortDescription,
                    fullDefinition: cached.longDescription || undefined,
                    tags: cached.tags.length > 0 ? cached.tags : undefined,
                    authentikSpecific: cached.authentikSpecific,
                };
            })
            .filter((term): term is NonNullable<typeof term> => term !== null);
    }, [glossaryPool, termCache]);

    // Optimized render function with memoized term lookup
    const renderTerms = useCallback(
        (
            filteredTerms: GlossaryHelperTerm[],
            viewMode: "categorized" | "alphabetical",
            searchFilter: string,
        ) => {
            if (viewMode === "categorized") {
                // Categorized view: group terms by their tags into sections
                const termsByTag = groupByTag(filteredTerms);
                return termsByTag.map(([tag, tagTerms]) => (
                    <div key={tag} className={glossaryStyles.section}>
                        <h2 className={glossaryStyles.sectionTitle}>{formatTag(tag)}</h2>
                        <section className={clsx("row")}>
                            {tagTerms.map((term) => {
                                const sidebarItem = sidebarItemMap.get(term.id);
                                return sidebarItem ? (
                                    <GlossaryTermCard
                                        key={term.id}
                                        item={sidebarItem}
                                        termCache={termCache}
                                        searchFilter={searchFilter}
                                    />
                                ) : null;
                            })}
                        </section>
                    </div>
                ));
            }
            // Alphabetical view: group terms by first letter A-Z
            const termsByAlphabet = groupByFirstLetter(filteredTerms);
            return termsByAlphabet.map(([letter, letterTerms]) => (
                <div
                    key={letter}
                    className={glossaryStyles.simplifiedSection}
                    id={`letter-${letter}`}
                >
                    <h2 className={glossaryStyles.sectionTitle}>{letter}</h2>
                    <section className={clsx("row")}>
                        {letterTerms.map((term) => {
                            const sidebarItem = sidebarItemMap.get(term.id);
                            return sidebarItem ? (
                                <GlossaryTermCard
                                    key={term.id}
                                    item={sidebarItem}
                                    termCache={termCache}
                                    searchFilter={searchFilter}
                                />
                            ) : null;
                        })}
                    </section>
                </div>
            ));
        },
        [sidebarItemMap, termCache],
    );

    return (
        <ErrorBoundary
            fallback={
                <div className="alert alert--warning margin-bottom--md">
                    <h4>Glossary temporarily unavailable</h4>
                    <p>
                        There was an error loading the glossary terms. Please try refreshing the
                        page.
                    </p>
                </div>
            }
        >
            <GlossaryHelper terms={glossaryTerms} className={className}>
                {renderTerms}
            </GlossaryHelper>
        </ErrorBoundary>
    );
}
