// Shared utilities and types
import { type GlossaryItem, isGlossaryItem, isGlossaryPath } from "../utils/glossaryUtils";
import { isLearningCenterItem, isLearningCenterPath } from "../utils/learningCenterUtils";
import ErrorBoundary from "./ErrorBoundary";
import GlossaryDocCardList from "./GlossaryDocCardList";
import LearningCenterDocCardList from "./LearningCenterDocCardList";
import styles from "./styles.module.css";

// Docusaurus core imports
import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";
import * as DocsClient from "@docusaurus/plugin-content-docs/client";
import {
    filterDocCardListItems,
    useCurrentSidebarSiblings,
} from "@docusaurus/plugin-content-docs/client";
import { useLocation } from "@docusaurus/router";
import DocCard from "@theme/DocCard";
import type { Props } from "@theme/DocCardList";
import clsx from "clsx";
import React, { ReactNode, useMemo } from "react";

// Constant empty array to avoid creating new array on each render
const EMPTY_SIDEBAR_ITEMS: PropSidebarItem[] = [];

// Type aliases for clarity
type SidebarDocLike = Extract<PropSidebarItem, { type: "link" }>;
const EMPTY_LINK_ITEMS: SidebarDocLike[] = [];

interface DocsSidebarContext {
    items: PropSidebarItem[];
}

const useDocsSidebarSafe: () => DocsSidebarContext | null =
    (DocsClient as unknown as { useDocsSidebar?: () => DocsSidebarContext | null })
        .useDocsSidebar ?? (() => null);

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
function getStableKey(item: GlossaryItem | PropSidebarItem, idx: number): string | number {
    if (typeof item === "object" && item !== null) {
        const match = ["docId", "id", "href", "label"].find(
            (name) => hasOwnProperty(item, name) && typeof item[name] === "string",
        );
        return match ? ((item as Record<string, unknown>)[match] as string) : idx;
    }
    return idx;
}

/**
 * Recursively collect sidebar link items matching a predicate.
 */
function collectSidebarLinks(
    items: readonly PropSidebarItem[],
    match: (item: PropSidebarItem) => boolean,
): SidebarDocLike[] {
    const collected: SidebarDocLike[] = [];

    const process = (item: PropSidebarItem) => {
        if (item.type === "link" && match(item)) {
            collected.push(item as SidebarDocLike);
            return;
        }
        if (item.type === "category" && item.items) {
            item.items.forEach(process);
        }
    };

    items.forEach(process);
    return collected;
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
 * Provides both standard documentation card rendering and specialized glossary/learning center functionality.
 */
export default function DocCardList(props: Props): ReactNode {
    const { items, className } = props;

    const pathname = useLocation()?.pathname ?? "";
    const isGlossary = isGlossaryPath(pathname);
    const isLearningCenter = isLearningCenterPath(pathname);

    const sidebarSiblings = useCurrentSidebarSiblings();
    const siblings = sidebarSiblings ?? EMPTY_SIDEBAR_ITEMS;
    const docsSidebar = useDocsSidebarSafe();
    const fullSidebarItems = docsSidebar?.items ?? EMPTY_SIDEBAR_ITEMS;

    // Extract glossary terms from sidebar structure when on glossary pages.
    const glossaryPool = useMemo<SidebarDocLike[]>(() => {
        if (!isGlossary) {
            return EMPTY_LINK_ITEMS;
        }
        return collectSidebarLinks(siblings, isGlossaryItem);
    }, [isGlossary, siblings]);

    // Extract learning center resources from sidebar structure when on learning center pages.
    const resourcePool = useMemo<SidebarDocLike[]>(() => {
        if (!isLearningCenter) {
            return EMPTY_LINK_ITEMS;
        }

        // On learning-path detail pages, current siblings can be limited to the
        // "path" category only. Use full sidebar tree for complete resource extraction.
        const allItems = fullSidebarItems.length > 0 ? fullSidebarItems : (items ?? siblings);
        return collectSidebarLinks(allItems, isLearningCenterItem);
    }, [fullSidebarItems, isLearningCenter, items, siblings]);

    // Standard documentation card items for non-specialized pages.
    const baseItems = useMemo(() => filterDocCardListItems(items ?? siblings), [items, siblings]);

    // For glossary pages, delegate to specialized GlossaryDocCardList component
    if (isGlossary) {
        return (
            <ErrorBoundary>
                <GlossaryDocCardList glossaryPool={glossaryPool} className={className} />
            </ErrorBoundary>
        );
    }

    // For learning center pages, delegate to specialized LearningCenterDocCardList component
    if (isLearningCenter) {
        return (
            <ErrorBoundary>
                <LearningCenterDocCardList resourcePool={resourcePool} className={className} />
            </ErrorBoundary>
        );
    }

    // Standard documentation card rendering for non-specialized pages
    return (
        <section className={clsx("row", className)}>
            {baseItems.map((item, idx) => (
                <DocCardListItem key={getStableKey(item, idx)} item={item} />
            ))}
        </section>
    );
}

export { DocCardList };
