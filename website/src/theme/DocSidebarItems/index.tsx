import {
    DocSidebarItemsExpandedStateProvider,
    useVisibleSidebarItems,
} from "@docusaurus/plugin-content-docs/client";
import { VersionPicker } from "@site/src/components/VersionPicker/index";
import DocSidebarItem from "@theme/DocSidebarItem";
import type { Props as DocSidebarItemsProps } from "@theme/DocSidebarItems";
import { memo } from "react";

const DocSidebarItems: React.FC<DocSidebarItemsProps> = ({ items, ...props }) => {
    const visibleItems = useVisibleSidebarItems(items, props.activePath);
    const includeVersionPicker = props.level === 1 && props.activePath.startsWith("/docs");

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
