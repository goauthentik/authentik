import glossaryStyles from "../../components/Glossary/styles.module.css";
import { formatTag, groupByFirstLetter, groupByTag } from "../../components/Glossary/utils";
import {
    type GlossaryHelperTerm,
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
 * Converts backticks to HTML code elements
 */
function renderMarkdown(text: string): string {
    return text.replace(/`([^`]+)`/g, "<code>$1</code>");
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

    const { termName, tags, shortDescription, longDescription } = cachedData;
    const longParagraphs = splitParagraphs(longDescription);
    const hasLongDescription = longParagraphs.length > 0;

    return (
        <article
            className={clsx(styles.docCardListItem, sharedStyles.cardContainer, "col col--12")}
            data-tags={tags.join(",")}
        >
            <div className="card margin-bottom--md">
                <div className="card__header">
                    <h3 className="margin-vert--sm" aria-label={termName || "Glossary term"}>
                        {termName || "Glossary term"}
                    </h3>
                </div>
                <div className="card__body">
                    <div
                        className={clsx(
                            sharedStyles.glossaryShort,
                            !shortDescription && sharedStyles.glossaryShortMissing,
                        )}
                        dangerouslySetInnerHTML={{
                            __html: shortDescription
                                ? renderMarkdown(shortDescription)
                                : "Short description not provided.",
                        }}
                    />

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
                                        <p
                                            key={index}
                                            dangerouslySetInnerHTML={{
                                                __html: renderMarkdown(paragraph),
                                            }}
                                        />
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
