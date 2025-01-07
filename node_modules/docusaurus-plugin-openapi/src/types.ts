/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import type { MDXOptions } from "@docusaurus/mdx-loader";
import type { TagsPluginOptions } from "@docusaurus/utils";
import type { Request } from "postman-collection";

import {
  InfoObject,
  OperationObject,
  SecuritySchemeObject,
} from "./openapi/types";

export type {
  PropSidebarItemCategory,
  SidebarItemLink,
  PropSidebar,
  PropSidebarItem,
} from "@docusaurus/plugin-content-docs-types";
export interface PluginOptions extends MDXOptions, TagsPluginOptions {
  id: string;
  path: string;
  routeBasePath: string;
  apiLayoutComponent: string;
  apiItemComponent: string;
  admonitions:
    | boolean
    // AdmonitionOptions is not exported from @docusaurus/mdx-loader
    | {
        tag: string;
        keywords: string[];
      };
  sidebarCollapsible: boolean;
  sidebarCollapsed: boolean;
}

export interface LoadedContent {
  loadedApi: ApiMetadata[];
}

export type ApiMetadata = ApiPageMetadata | InfoPageMetadata | MdxPageMetadata;

export interface ApiMetadataBase {
  sidebar?: string;
  previous?: ApiNavLink;
  next?: ApiNavLink;
  //
  id: string; // TODO legacy versioned id => try to remove
  title: string;
  description: string;
  source: string; // @site aliased source => "@site/docs/folder/subFolder/subSubFolder/myDoc.md"
  sourceDirName: string; // relative to the versioned docs folder (can be ".") => "folder/subFolder/subSubFolder"
  slug: string;
  permalink: string;
  sidebarPosition?: number;
  frontMatter: Record<string, unknown>;
}

export interface ApiPageMetadata extends ApiMetadataBase {
  type: "api";
  api: ApiItem;
}

export interface ApiItem extends OperationObject {
  method: string; // get, post, put, etc...
  path: string; // The endpoint path => "/api/getPets"
  jsonRequestBodyExample: string;
  securitySchemes?: {
    [key: string]: SecuritySchemeObject;
  };
  postman?: Request;
  info: InfoObject;
}

export interface InfoPageMetadata extends ApiMetadataBase {
  type: "info";
  info: ApiInfo;
}

export interface MdxPageMetadata extends ApiMetadataBase {
  type: "mdx";
}

export type ApiInfo = InfoObject;

export interface ApiNavLink {
  title: string;
  permalink: string;
}
