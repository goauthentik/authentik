import "./styles.css";

import { isGlossaryItem } from "../utils/glossaryUtils";
import { shouldFilterFromSidebar as shouldFilterLearningCenterItem } from "../utils/learningCenter/utils";

import { VersionPicker } from "#components/VersionPicker/index.tsx";

import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";
import {
    DocSidebarItemsExpandedStateProvider,
    isVisibleSidebarItem,
} from "@docusaurus/plugin-content-docs/client";
import DocSidebarItem from "@theme/DocSidebarItem";
import type { Props as DocSidebarItemsProps } from "@theme/DocSidebarItems";
import { JSX, memo, useMemo } from "react";

function isReleaseNotesItem(item: PropSidebarItem): boolean {
    return !!(item.type === "link" && item.docId?.startsWith("releases"));
}

function getSidebarItemKey(item: PropSidebarItem, fallbackIndex: number): string {
    if (item.type === "link") {
        return item.docId || item.href || item.label || String(fallbackIndex);
    }
    if (item.type === "category") {
        return item.label || item.href || String(fallbackIndex);
    }
    return String(fallbackIndex);
}

function useVisibleSidebarItems(
    items: readonly PropSidebarItem[],
    activePath: string,
): PropSidebarItem[] {
    return useMemo(
        () =>
            items.filter((item) => {
                return isVisibleSidebarItem(item, activePath) || isReleaseNotesItem(item);
            }),
        [items, activePath],
    );
}

const DocSidebarItems = ({ items, ...props }: DocSidebarItemsProps): JSX.Element => {
    const visibleItems = useVisibleSidebarItems(items, props.activePath);
    const navigableItems = useMemo(
        () =>
            visibleItems.filter(
                (item) => !isGlossaryItem(item) && !shouldFilterLearningCenterItem(item),
            ),
        [visibleItems],
    );

    const includeVersionPicker = props.level === 1 && !props.activePath.startsWith("/integrations");

    return (
        <DocSidebarItemsExpandedStateProvider>
            {includeVersionPicker ? <VersionPicker /> : null}
            {navigableItems.map((item, index) => {
                return (
                    <DocSidebarItem
                        key={getSidebarItemKey(item, index)}
                        item={item}
                        index={index}
                        {...props}
                    />
                );
            })}
        </DocSidebarItemsExpandedStateProvider>
    );
};

export default memo(DocSidebarItems);
