/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import type { OptionValidationContext } from "@docusaurus/types";
import {
  Joi,
  RemarkPluginsSchema,
  RehypePluginsSchema,
  RecmaPluginsSchema,
  AdmonitionsSchema,
} from "@docusaurus/utils-validation";
import chalk from "chalk";

import type { PluginOptions } from "./types";

export const DEFAULT_OPTIONS: Omit<PluginOptions, "id" | "sidebarPath"> = {
  path: "openapi.json", // Path to data on filesystem, relative to site dir.
  routeBasePath: "api", // URL Route.
  apiLayoutComponent: "@theme/ApiPage",
  apiItemComponent: "@theme/ApiItem",
  remarkPlugins: [],
  rehypePlugins: [],
  recmaPlugins: [],
  beforeDefaultRemarkPlugins: [],
  beforeDefaultRehypePlugins: [],
  admonitions: true,
  sidebarCollapsible: true,
  sidebarCollapsed: true,
  onInlineTags: "warn",
  tags: undefined,
};

export const OptionsSchema = Joi.object<PluginOptions>({
  path: Joi.string().default(DEFAULT_OPTIONS.path),
  routeBasePath: Joi.string()
    // '' not allowed, see https://github.com/facebook/docusaurus/issues/3374
    // .allow('') ""
    .default(DEFAULT_OPTIONS.routeBasePath),
  sidebarCollapsible: Joi.boolean().default(DEFAULT_OPTIONS.sidebarCollapsible),
  sidebarCollapsed: Joi.boolean().default(DEFAULT_OPTIONS.sidebarCollapsed),
  apiLayoutComponent: Joi.string().default(DEFAULT_OPTIONS.apiLayoutComponent),
  apiItemComponent: Joi.string().default(DEFAULT_OPTIONS.apiItemComponent),
  remarkPlugins: RemarkPluginsSchema.default(DEFAULT_OPTIONS.remarkPlugins),
  rehypePlugins: RehypePluginsSchema.default(DEFAULT_OPTIONS.rehypePlugins),
  recmaPlugins: RecmaPluginsSchema.default(DEFAULT_OPTIONS.recmaPlugins),
  beforeDefaultRemarkPlugins: RemarkPluginsSchema.default(
    DEFAULT_OPTIONS.beforeDefaultRemarkPlugins
  ),
  beforeDefaultRehypePlugins: RehypePluginsSchema.default(
    DEFAULT_OPTIONS.beforeDefaultRehypePlugins
  ),
  admonitions: Joi.alternatives()
    .try(AdmonitionsSchema, Joi.boolean().invalid(true))
    .default(DEFAULT_OPTIONS.admonitions),
  onInlineTags: Joi.string()
    .equal("ignore", "log", "warn", "throw")
    .default(DEFAULT_OPTIONS.onInlineTags),
  tags: Joi.string()
    .disallow("")
    .allow(null, false)
    .default(() => DEFAULT_OPTIONS.tags),
});

export function validateOptions({
  validate,
  options: userOptions,
}: OptionValidationContext<PluginOptions, PluginOptions>): PluginOptions {
  let options = userOptions;

  if (options.sidebarCollapsible === false) {
    // When sidebarCollapsible=false and sidebarCollapsed=undefined, we don't want to have the inconsistency warning
    // We let options.sidebarCollapsible become the default value for options.sidebarCollapsed
    if (typeof options.sidebarCollapsed === "undefined") {
      options = {
        ...options,
        sidebarCollapsed: false,
      };
    }
    if (options.sidebarCollapsed) {
      console.warn(
        chalk.yellow(
          "The docs plugin config is inconsistent. It does not make sense to use sidebarCollapsible=false and sidebarCollapsed=true at the same time. sidebarCollapsed=false will be ignored."
        )
      );
      options = {
        ...options,
        sidebarCollapsed: false,
      };
    }
  }

  const normalizedOptions = validate(OptionsSchema, options);

  return normalizedOptions;
}
