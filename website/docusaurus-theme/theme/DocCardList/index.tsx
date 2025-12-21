// Shared utilities and types
import { type GlossaryItem, isGlossaryItem, isGlossaryPath } from "../utils/glossaryUtils";
import ErrorBoundary from "./ErrorBoundary";
import GlossaryDocCardList from "./GlossaryDocCardList";
import styles from "./styles.module.css";

// Docusaurus core imports
import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";
import {
    filterDocCardListItems,
    useCurrentSidebarSiblings,
} from "@docusaurus/plugin-content-docs/client";
import { useLocation } from "@docusaurus/router";
import DocCard from "@theme/DocCard";
import type { Props } from "@theme/DocCardList";
import clsx from "clsx";
import React, { ReactNode, useMemo } from "react";

// Type aliases for clarity
type SidebarDocLike = Extract<PropSidebarItem, { type: "link" }>;

/**
 * Type-safe property existence checker with proper typing
 */
function hasOwnProperty<T extends object, K extends PropertyKey>(
    value: T,
    key: K,
): value is T & Record<K, unknown> {
    return Object.prototype.hasOwnProperty.call(value, key);
}

/**
 * Generates stable React keys from sidebar items, with fallback to index
 */
function getStableKey(item: GlossaryItem | PropSidebarItem, idx: number) {
    if (typeof item === "object" && item !== null) {
        const match = ["docId", "id", "href", "label"].find(
            (name) => hasOwnProperty(item, name) && typeof item[name] === "string",
        );
        return match ? item[match] : idx;
    }
    return idx;
}

/**
 * Standard documentation card item for non-glossary content
 */
function DocCardListItem({ item }: { item: React.ComponentProps<typeof DocCard>["item"] }) {
    return (
        <article className={clsx(styles.docCardListItem, "col col--6")}>
            <DocCard item={item} />
        </article>
    );
}

/**
 * Enhanced DocCardList component that delegates to specialized components based on content type.
 * Provides both standard documentation card rendering and specialized glossary functionality.
 */
export default function DocCardList(props: Props): ReactNode {
    const { items, className } = props;

    const pathname = useLocation()?.pathname ?? "";
    const isGlossary = isGlossaryPath(pathname);

    const siblings = useCurrentSidebarSiblings() ?? [];

    // For glossary pages, delegate to specialized GlossaryDocCardList component
    if (isGlossary) {
        // Extract glossary terms from sidebar structure
        const glossaryPool = useMemo<SidebarDocLike[]>(() => {
            const terms: SidebarDocLike[] = [];

            // Recursively process sidebar items to find glossary terms
            const processItem = (item: PropSidebarItem) => {
                if (isGlossaryItem(item) && item.type === "link") {
                    terms.push(item as SidebarDocLike);
                } else if (item.type === "category" && item.items) {
                    item.items.forEach(processItem);
                }
            };

            siblings.forEach(processItem);
            return terms;
        }, [siblings]);

        return (
            <ErrorBoundary>
                <GlossaryDocCardList glossaryPool={glossaryPool} className={className} />
            </ErrorBoundary>
        );
    }

    // Standard documentation card rendering for non-glossary pages
    const baseItems = useMemo(() => filterDocCardListItems(items ?? siblings), [items, siblings]);

    return (
        <section className={clsx("row", className)}>
            {baseItems.map((item, idx) => (
                <DocCardListItem key={getStableKey(item, idx)} item={item} />
            ))}
        </section>
    );
}

export { DocCardList };
