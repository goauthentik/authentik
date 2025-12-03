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
        isAuthentikSpecific: boolean;
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
 * Converts backticks to code elements
 */
function renderMarkdown(text: string): (string | React.ReactElement)[] {
    const parts: (string | React.ReactElement)[] = [];
    const regex = /`([^`]+)`/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
        // Add text before the match
        if (match.index > lastIndex) {
            parts.push(text.substring(lastIndex, match.index));
        }
        // Add the code element
        parts.push(<code key={match.index}>{match[1]}</code>);
        lastIndex = regex.lastIndex;
    }

    // Add remaining text
    if (lastIndex < text.length) {
        parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : [text];
}

/**
 * Renders a single glossary term as a card with title, short description, and long description.
 */
function GlossaryTermCard({ item, termCache }: { item: SidebarDocLike; termCache: TermCache }) {
    const [isExpanded, setIsExpanded] = React.useState(false);

    // Ensure item has a valid docId before accessing cache
    if (!item.docId) {
        console.error(`DocCardList: glossary item missing docId:`, item);
        return null;
    }

    const cachedData = termCache[item.docId];

    if (!cachedData) {
        console.error(`DocCardList: no cached data found for glossary term '${item.docId}'.`);
        return null;
    }

    const { termName, tags, shortDescription, longDescription, isAuthentikSpecific } = cachedData;
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
                        {termName || "Glossary term"}
                        {isAuthentikSpecific && (
                            <span
                                className={sharedStyles.authentikBadge}
                                title="authentik-specific term"
                            >
                                authentik specific
                            </span>
                        )}
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
                            ? renderMarkdown(shortDescription)
                            : "Short description not provided."}
                    </div>

                    {hasLongDescription && (
                        <>
                            <button
                                className={sharedStyles.expandButton}
                                onClick={() => setIsExpanded(!isExpanded)}
                                aria-expanded={isExpanded}
                            >
                                {isExpanded ? "▼ Hide details" : "▶ Show details"}
                            </button>
                            {isExpanded && (
                                <div className={sharedStyles.glossaryLong}>
                                    {longParagraphs.map((paragraph, index) => (
                                        <p key={index}>{renderMarkdown(paragraph)}</p>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
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
        const queryString = window.location.search;
        if (queryString && queryString.length > 1) {
            const termId = queryString.substring(1); // Remove the '?'

            // Function to scroll to element
            const scrollToTerm = () => {
                const element = document.getElementById(termId);
                if (element) {
                    element.scrollIntoView({ behavior: "smooth", block: "start" });
                    return true;
                }
                return false;
            };

            // Try immediately
            if (!scrollToTerm()) {
                // If not found, try after a delay to allow DOM to render
                const timeoutId = setTimeout(() => {
                    scrollToTerm();
                }, 100);

                return () => clearTimeout(timeoutId);
            }
        }
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
                    isAuthentikSpecific: safeBooleanExtract(sidebarProps.isAuthentikSpecific),
                };
            });

        return cache;
    }, [glossaryPool]);

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
                    isAuthentikSpecific: cached.isAuthentikSpecific,
                };
            })
            .filter((term): term is NonNullable<typeof term> => term !== null);
    }, [glossaryPool, termCache]);

    // Optimized render function with memoized term lookup
    const renderTerms = useCallback(
        (filteredTerms: GlossaryHelperTerm[], viewMode: "categorized" | "alphabetical") => {
            if (viewMode === "categorized") {
                // Categorized view: group terms by their tags into sections
                const termsByTag = groupByTag(filteredTerms);
                return (
                    <>
                        {termsByTag.map(([tag, tagTerms]) => (
                            <div key={tag} className={glossaryStyles.section}>
                                <h2 className={glossaryStyles.sectionTitle}>{formatTag(tag)}</h2>
                                <section className={clsx("row")}>
                                    {tagTerms.map((term) => {
                                        // Use pre-cached sidebar item lookup
                                        const sidebarItem = glossaryPool.find(
                                            (item) => item.docId === term.id,
                                        );
                                        return sidebarItem && sidebarItem.docId ? (
                                            <GlossaryTermCard
                                                key={term.id}
                                                item={sidebarItem}
                                                termCache={termCache}
                                            />
                                        ) : null;
                                    })}
                                </section>
                            </div>
                        ))}
                    </>
                );
            } else {
                // Alphabetical view: group terms by first letter A-Z
                const termsByAlphabet = groupByFirstLetter(filteredTerms);
                return (
                    <>
                        {termsByAlphabet.map(([letter, letterTerms]) => (
                            <div
                                key={letter}
                                className={glossaryStyles.simplifiedSection}
                                id={`letter-${letter}`}
                            >
                                <h2 className={glossaryStyles.sectionTitle}>{letter}</h2>
                                <section className={clsx("row")}>
                                    {letterTerms.map((term) => {
                                        // Use pre-cached sidebar item lookup
                                        const sidebarItem = glossaryPool.find(
                                            (item) => item.docId === term.id,
                                        );
                                        return sidebarItem && sidebarItem.docId ? (
                                            <GlossaryTermCard
                                                key={term.id}
                                                item={sidebarItem}
                                                termCache={termCache}
                                            />
                                        ) : null;
                                    })}
                                </section>
                            </div>
                        ))}
                    </>
                );
            }
        },
        [glossaryPool, termCache],
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
