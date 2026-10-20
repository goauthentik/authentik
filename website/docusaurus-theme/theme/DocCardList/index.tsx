import styles from "./styles.module.css";

// Docusaurus core imports
import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";
import {
    filterDocCardListItems,
    useCurrentSidebarSiblings,
    useDocById,
} from "@docusaurus/plugin-content-docs/client";
import DocCard from "@theme/DocCard";
import Layout from "@theme/DocCard/Layout";
import type { Props } from "@theme/DocCardList";
import clsx from "clsx";
import React, { ReactNode, useMemo } from "react";

// Constant empty array to avoid creating new array on each render
const EMPTY_SIDEBAR_ITEMS: PropSidebarItem[] = [];

// Type aliases for clarity
type SidebarDocLike = Extract<PropSidebarItem, { type: "link" }>;

function isReleaseDocLink(item: PropSidebarItem): item is SidebarDocLike {
    return item.type === "link" && !!item.docId?.startsWith("releases/");
}

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
function getStableKey(item: PropSidebarItem, idx: number): string | number {
    if (typeof item === "object" && item !== null) {
        const match = ["docId", "id", "href", "label"].find(
            (name) => hasOwnProperty(item, name) && typeof item[name] === "string",
        );
        return match ? ((item as Record<string, unknown>)[match] as string) : idx;
    }
    return idx;
}

/**
 * Release documentation card item
 */
function ReleaseDocCard({ item }: { item: SidebarDocLike }) {
    const doc = useDocById(item.docId ?? undefined);

    // Docusaurus treats leading digits as emoji-like graphemes and splits the
    // "2" out into the card icon slot, making version labels look broken.
    return (
        <Layout
            item={item}
            className={item.className}
            href={item.href}
            icon={null}
            title={item.label}
            description={item.description ?? doc?.description}
        />
    );
}

/**
 * Standard documentation card item
 */
function DocCardListItem({ item }: { item: React.ComponentProps<typeof DocCard>["item"] }) {
    return (
        <article className={clsx(styles.docCardListItem, "col col--6")}>
            {isReleaseDocLink(item) ? <ReleaseDocCard item={item} /> : <DocCard item={item} />}
        </article>
    );
}

/**
 * DocCardList that renders release notes without Docusaurus's emoji icon slot.
 */
export default function DocCardList(props: Props): ReactNode {
    const { items, className } = props;

    const sidebarSiblings = useCurrentSidebarSiblings();
    const siblings = sidebarSiblings ?? EMPTY_SIDEBAR_ITEMS;

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
