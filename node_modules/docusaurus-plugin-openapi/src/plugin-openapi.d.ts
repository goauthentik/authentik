/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

// TODO: figure out how to import this
declare module "@docusaurus/plugin-content-docs-types" {
  // Makes all properties visible when hovering over the type
  type Expand<T extends Record<string, unknown>> = { [P in keyof T]: T[P] };

  export type SidebarItemBase = {
    className?: string;
    customProps?: Record<string, unknown>;
    position?: number;
  };

  export type SidebarItemLink = SidebarItemBase & {
    type: "link";
    href: string;
    label: string;
    docId: string;
  };

  type SidebarItemCategoryBase = SidebarItemBase & {
    type: "category";
    label: string;
    collapsed: boolean;
    collapsible: boolean;
  };

  export type PropSidebarItemCategory = Expand<
    SidebarItemCategoryBase & {
      items: PropSidebarItem[];
    }
  >;

  export type PropSidebarItem = SidebarItemLink | PropSidebarItemCategory;
  export type PropSidebar = PropSidebarItem[];
  export type PropSidebars = {
    [sidebarId: string]: PropSidebar;
  };
}

declare module "docusaurus-plugin-openapi" {
  import type { PropSidebars } from "@docusaurus/plugin-content-docs-types";

  export type Options = Partial<import("./types").PluginOptions>;

  export type PropApiMetadata = {
    // TODO: adjust this to our needs
    pluginId: string;
    version: string;
    label: string;
    banner: VersionBanner | null;
    badge: boolean;
    className: string;
    isLast: boolean;
    apiSidebars: PropSidebars;
  };
}

declare module "@theme/ApiPage" {
  import type { ApiRoute } from "@theme/ApiItem";
  import type { PropApiMetadata } from "docusaurus-plugin-openapi";

  export interface Props {
    readonly location: { readonly pathname: string };
    readonly apiMetadata: PropApiMetadata;
    readonly route: {
      readonly path: string;
      readonly component: () => JSX.Element;
      readonly routes: ApiRoute[];
    };
  }

  const ApiPage: (props: Props) => JSX.Element;
  export default ApiPage;
}

declare module "@theme/ApiItem" {
  import type { Request } from "postman-collection";

  import type { ApiItem } from "./types";

  export type ApiRoute = {
    readonly component: () => JSX.Element;
    readonly exact: boolean;
    readonly path: string;
    readonly sidebar?: string;
  };

  export type FrontMatter = {
    readonly id: string;
    readonly title: string;
    readonly image?: string;
    readonly keywords?: readonly string[];
  };

  export type Metadata = {
    readonly description?: string;
    readonly title?: string;
    readonly permalink?: string;
    readonly previous?: { readonly permalink: string; readonly title: string };
    readonly next?: { readonly permalink: string; readonly title: string };
    readonly api?: ApiItem & { postman: Request }; // TODO
  };

  export interface Props {
    readonly route: ApiRoute;
    readonly content: {
      readonly frontMatter: FrontMatter;
      readonly metadata: Metadata;
      readonly contentTitle: string | undefined;
      (): JSX.Element;
    };
  }

  const ApiItem: (props: Props) => JSX.Element;
  export default ApiItem;
}

declare module "@theme/MarkdownItem" {
  export interface Props {
    readonly content: {
      readonly metadata: Metadata;
      (): JSX.Element;
    };
  }

  const MarkdownItem: (props: Props) => JSX.Element;
  export default MarkdownItem;
}

declare module "@theme/ApiDemoPanel" {
  import type { Metadata } from "@theme/ApiItem";

  export interface Props {
    readonly item: NonNullable<Metadata["api"]>;
  }

  const ApiDemoPanel: (props: Props) => JSX.Element;
  export default ApiDemoPanel;
}

declare module "@theme/ApiDemoPanel/Curl" {
  import type { Request } from "postman-collection";

  export interface Props {
    readonly postman: Request;
    readonly codeSamples: Array<Any>;
  }

  const Curl: (props: Props) => JSX.Element;
  export default Curl;
}

declare module "@theme/ApiDemoPanel/Response" {
  const Response: () => JSX.Element;
  export default Response;
}
