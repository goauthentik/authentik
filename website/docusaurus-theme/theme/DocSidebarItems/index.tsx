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
    debugger;
    console.debug("[DocSidebarItems] activePath:", props.activePath, "isGlossary:", isGlossary);

    const filteredVisibleItems = isGlossary
        ? visibleItems.filter((it: any) => {
              const href = typeof it?.href === "string" ? it.href : "";
              const label = typeof it?.label === "string" ? it.label.toLowerCase() : "";
              const isCategory = it?.type === "category";
              const isLeaf = !isCategory;
              const isTermsCategory = isCategory && (label === "terms" || href.includes("/glossary/terms") || href.endsWith("/terms"));
              const isTermsLeaf = isLeaf && href.includes("/glossary/terms/");
              const shouldSkip = isTermsCategory || isTermsLeaf;
              if (shouldSkip) {
                  console.debug("[DocSidebarItems] skipping glossary item:", {
                      type: it?.type,
                      label: it?.label,
                      href,
                      isCategory,
                      isTermsCategory,
                      isTermsLeaf,
                  });
              }
              return !shouldSkip;
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
