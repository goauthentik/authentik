/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { basename, join, extname } from "node:path";

import { CategoryMetadataFile } from "@docusaurus/plugin-content-docs/lib/sidebars/types";
import { posixPath } from "@docusaurus/utils";
import chalk from "chalk";
import clsx from "clsx";
import Yaml from "js-yaml";
import { groupBy, sortBy, uniq } from "lodash";
import type { DeepPartial } from "utility-types";

import type {
  InfoPageMetadata,
  MdxPageMetadata,
  PropSidebar,
  PropSidebarItem,
  PropSidebarItemCategory,
} from "../types";
import { ApiPageMetadata } from "../types";

interface Options {
  contentPath: string;
  sidebarCollapsible: boolean;
  sidebarCollapsed: boolean;
}

type keys = "type" | "title" | "permalink" | "id" | "source" | "sourceDirName";

type InfoItem = Pick<InfoPageMetadata, keys>;
type ApiItem = Pick<ApiPageMetadata, keys> & {
  api: DeepPartial<ApiPageMetadata["api"]>;
};
type MdxItem = Pick<MdxPageMetadata, keys | "frontMatter">;

type Item = InfoItem | ApiItem | MdxItem;

const CategoryMetadataFilenameBase = "_category_";

const BottomSidebarPosition = 999999;

function isApiItem(item: Item): item is ApiItem {
  return item.type === "api";
}

function isInfoItem(item: Item): item is InfoItem {
  return item.type === "info";
}

function isMdxItem(item: Item): item is MdxItem {
  return item.type === "mdx";
}

const Terminator = "."; // a file or folder can never be "."
const BreadcrumbSeparator = "/";
function getBreadcrumbs(dir: string) {
  if (dir === Terminator) {
    // this isn't actually needed, but removing would result in an array: [".", "."]
    return [Terminator];
  }
  return [...dir.split(BreadcrumbSeparator).filter(Boolean), Terminator];
}

export async function generateSidebar(
  items: Item[],
  options: Options
): Promise<PropSidebar> {
  const sourceGroups = groupBy(items, (item) => item.source);

  let sidebar: PropSidebar = [];
  let visiting = sidebar;
  for (const items of Object.values(sourceGroups)) {
    if (items.length === 0) {
      // Since the groups are created based on the items, there should never be a length of zero.
      console.warn(chalk.yellow(`Unnexpected empty group!`));
      continue;
    }

    const { sourceDirName, source } = items[0];

    const breadcrumbs = getBreadcrumbs(sourceDirName);

    let currentPath = [];
    for (const crumb of breadcrumbs) {
      // We hit a spec file, create the groups for it.
      if (crumb === Terminator) {
        if (isMdxItem(items[0])) {
          visiting.push(...groupByTags(items, options));
        } else if (
          ["_spec_.json", "_spec_.yml", "_spec_.yaml"].includes(
            basename(items[0].source)
          )
        ) {
          // Don't create a category for this spec file
          visiting.push(...groupByTags(items, options));
        } else {
          const title = items.filter(isApiItem)[0]?.api.info?.title;
          const fileName = basename(source, extname(source));
          // Title could be an empty string so `??` won't work here.
          const label = !title ? fileName : title;
          visiting.push({
            type: "category" as const,
            label,
            position: BottomSidebarPosition,
            collapsible: options.sidebarCollapsible,
            collapsed: options.sidebarCollapsed,
            items: groupByTags(items, options),
          });
        }

        visiting = sidebar; // reset
        break;
      }

      // Read category file to generate a label for the current path.
      currentPath.push(crumb);
      const categoryPath = join(options.contentPath, ...currentPath);
      const meta = await readCategoryMetadataFile(categoryPath);
      const label = meta?.label ?? crumb;

      // Check for existing categories for the current label.
      const existingCategory = visiting
        .filter((c): c is PropSidebarItemCategory => c.type === "category")
        .find((c) => c.label === label);

      // If exists, skip creating a new one.
      if (existingCategory) {
        visiting = existingCategory.items;
        continue;
      }

      // Otherwise, create a new one.
      const newCategory = {
        type: "category" as const,
        className: meta?.className,
        customProps: meta?.customProps,
        position: meta?.position ?? BottomSidebarPosition,
        label,
        collapsible: meta?.collapsible ?? options.sidebarCollapsible,
        collapsed: meta?.collapsed ?? options.sidebarCollapsed,
        items: [],
      };
      visiting.push(newCategory);
      visiting = newCategory.items;
    }
  }

  // The first group should always be a category, but check for type narrowing
  if (sidebar.length === 1 && sidebar[0].type === "category") {
    return sidebar[0].items;
  }

  // Squash categories that only contain a single API spec
  if (sidebar.length > 0) {
    for (const item of sidebar) {
      if (
        item.type === "category" &&
        item.items.length === 1 &&
        item.items[0].type === "category"
      ) {
        item.items = item.items[0].items;
      }
    }
  }

  sidebar = recursiveSidebarSort(sidebar);

  return sidebar;
}

/**
 * Sort the sidebar recursively based on `position`.
 * @param sidebar
 * @returns
 */
function recursiveSidebarSort(sidebar: PropSidebar | PropSidebarItem[]) {
  // Use lodash sortBy to ensure sorting stability
  sidebar = sortBy(sidebar, (item) => item.position);
  for (const item of sidebar) {
    if (item.type === "category") {
      item.items = recursiveSidebarSort(item.items);
    }
  }
  return sidebar;
}

/**
 * Takes a flat list of pages and groups them into categories based on there tags.
 */
function groupByTags(items: Item[], options: Options): PropSidebar {
  const intros = items
    .filter((m) => isInfoItem(m) || isMdxItem(m))
    .map((item) => {
      const fileName = basename(item.source, extname(item.source));
      const label = !item.title ? fileName : item.title;

      return {
        type: "link" as const,
        label: label,
        href: item.permalink,
        docId: item.id,
        unlisted: false,
        position: isMdxItem(item)
          ? (item.frontMatter?.sidebar_position as number) ??
            BottomSidebarPosition
          : BottomSidebarPosition,
      };
    });

  const apiItems = items.filter(isApiItem);

  const tags = uniq(
    apiItems
      .flatMap((item) => item.api.tags)
      .filter((item): item is string => !!item)
  );

  function createLink(item: ApiItem) {
    return {
      type: "link" as const,
      label: item.title,
      href: item.permalink,
      docId: item.id,
      unlisted: false,
      className: clsx(
        {
          "menu__list-item--deprecated": item.api.deprecated,
          "api-method": !!item.api.method,
        },
        item.api.method
      ),
      position: BottomSidebarPosition,
    };
  }

  const tagged = tags
    .map((tag) => {
      return {
        type: "category" as const,
        label: tag,
        collapsible: options.sidebarCollapsible,
        collapsed: options.sidebarCollapsed,
        items: apiItems
          .filter((item) => !!item.api.tags?.includes(tag))
          .map(createLink),
        position: BottomSidebarPosition,
      };
    })
    .filter((item) => item.items.length > 0); // Filter out any categories with no items.

  let untagged = [
    {
      type: "category" as const,
      label: "API",
      collapsible: options.sidebarCollapsible,
      collapsed: options.sidebarCollapsed,
      items: apiItems
        .filter(({ api }) => api.tags === undefined || api.tags.length === 0)
        .map(createLink),
      position: BottomSidebarPosition,
    },
  ];

  if (untagged[0].items.length === 0) {
    untagged = [];
  }

  return [...intros, ...tagged, ...untagged];
}

/**
 * Taken from: https://github.com/facebook/docusaurus/blob/main/packages/docusaurus-plugin-content-docs/src/sidebars/generator.ts
 */
async function readCategoryMetadataFile(
  categoryDirPath: string
): Promise<CategoryMetadataFile | null> {
  async function tryReadFile(filePath: string): Promise<CategoryMetadataFile> {
    const contentString = await readFile(filePath, { encoding: "utf8" });
    const unsafeContent = Yaml.load(contentString);
    try {
      return unsafeContent as CategoryMetadataFile; // validateCategoryMetadataFile(unsafeContent);
    } catch (e) {
      console.error(
        chalk.red(
          `The docs sidebar category metadata file path=${filePath} looks invalid!`
        )
      );
      throw e;
    }
  }
  // eslint-disable-next-line no-restricted-syntax
  for (const ext of [".json", ".yml", ".yaml"]) {
    // Simpler to use only posix paths for mocking file metadata in tests
    const filePath = posixPath(
      join(categoryDirPath, `${CategoryMetadataFilenameBase}${ext}`)
    );
    if (existsSync(filePath)) {
      return tryReadFile(filePath);
    }
  }
  return null;
}
