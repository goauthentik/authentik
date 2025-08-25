/// <reference types="@docusaurus/plugin-content-docs" />
import "./styles.css";

import { VersionPicker } from "#components/VersionPicker/index.tsx";

import {
    DocSidebarItemsExpandedStateProvider,
    useVisibleSidebarItems,
} from "@docusaurus/plugin-content-docs/client";
import DocSidebarItem from "@theme/DocSidebarItem";
import type { Props as DocSidebarItemsProps } from "@theme/DocSidebarItems";
import { JSX, memo } from "react";

const DocSidebarItems = ({ items, ...props }: DocSidebarItemsProps): JSX.Element => {
    const visibleItems = useVisibleSidebarItems(items, props.activePath);
    const isGlossary = (props.activePath || "").includes("/glossary");

    const filteredVisibleItems = isGlossary
        ? visibleItems.filter((item) => {
              // Skip "terms" category entirely
              if (item.type === "category" && "label" in item && item.label === "terms") {
                  return false;
              }
              
              // Skip individual term documents
              if (item.type === "link" && "href" in item && item.href?.includes("/glossary/terms/")) {
                  return false;
              }
              
              return true;
          })
        : visibleItems;
    const includeVersionPicker = props.level === 1 && !props.activePath.startsWith("/integrations");
    
    return (
        <DocSidebarItemsExpandedStateProvider>
            {includeVersionPicker ? <VersionPicker /> : null}
            {filteredVisibleItems.map((item, index) => (
                <DocSidebarItem key={index} item={item} index={index} {...props} />
            ))}
        </DocSidebarItemsExpandedStateProvider>
    );
};

export default memo(DocSidebarItems);
