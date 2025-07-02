/// <reference types="@docusaurus/plugin-content-docs" />
import { VersionPicker } from "#components/VersionPicker/index.tsx";

import {
    DocSidebarItemsExpandedStateProvider,
    useVisibleSidebarItems,
} from "@docusaurus/plugin-content-docs/client";
import DocSidebarItem from "@theme/DocSidebarItem";
import type { Props as DocSidebarItemsProps } from "@theme/DocSidebarItems";
import { memo } from "react";

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
