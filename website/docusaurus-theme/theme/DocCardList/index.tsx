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

    // Extract glossary terms from sidebar structure (always computed, but only used for glossary pages)
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

    // Extract learning center resources from sidebar structure
    const resourcePool = useMemo<SidebarDocLike[]>(() => {
        const resources: SidebarDocLike[] = [];
        const seen = new Set<string>();

        // Recursively process sidebar items to find learning center resources
        const processItem = (item: PropSidebarItem) => {
            if (item.type === "link") {
                if (isLearningCenterItem(item)) {
                    const resourceItem = item as SidebarDocLike;
                    const key =
                        resourceItem.docId ||
                        resourceItem.href ||
                        ("label" in resourceItem && typeof resourceItem.label === "string"
                            ? resourceItem.label
                            : "");
                    if (!key || seen.has(key)) {
                        return;
                    }
                    seen.add(key);
                    resources.push(resourceItem);
                }
            } else if (item.type === "category" && item.items) {
                item.items.forEach(processItem);
            }
        };

        // On learning-path detail pages, current siblings can be limited to the
        // "path" category only. Use full sidebar tree for complete resource extraction.
        const allItems =
            isLearningCenter && fullSidebarItems.length > 0
                ? fullSidebarItems
                : (items ?? siblings);
        allItems.forEach(processItem);

        return resources;
    }, [fullSidebarItems, isLearningCenter, items, siblings]);

    // Standard documentation card items (always computed, but only used for non-specialized pages)
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
