import "./styles.css";

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

    const includeVersionPicker = props.level === 1 && !props.activePath.startsWith("/integrations");

    return (
        <DocSidebarItemsExpandedStateProvider>
            {includeVersionPicker ? <VersionPicker /> : null}
            {visibleItems.map((item, index) => (
                <DocSidebarItem key={index} item={item} index={index} {...props} />
            ))}
        </DocSidebarItemsExpandedStateProvider>
    );
};

export default memo(DocSidebarItems);
