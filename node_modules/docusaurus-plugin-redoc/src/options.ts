import { Joi } from '@docusaurus/utils-validation';
import type { RawConfig } from '@redocly/openapi-core';

type LayoutProps = {
  title?: string;
  noFooter?: boolean;
  description?: string;
  image?: string;
  keywords?: string[];
  permalink?: string;
  wrapperClassName?: string;
  searchMetadatas?: {
    version?: string;
    tag?: string;
  };
};

/**
 * Can pass only if directly using plugin.
 * `redocusaurus` auto populates them
 */
export interface PluginDirectUsageOptions {
  debug?: boolean;
  themeId?: string;
  /**
   * Redocly config to bundle file
   * @see https://redocly.com/docs/cli/configuration/configuration-file/
   */
  config?: string | RawConfig;
  layout?: LayoutProps;
}

export interface PluginOptions extends PluginDirectUsageOptions {
  id?: string;
  spec: string;
  url?: string;
  route?: string;
}

export interface PluginOptionsWithDefault extends PluginOptions {
  debug: boolean;
}

export const DEFAULT_OPTIONS = {
  layout: {},
  debug: false,
} satisfies Omit<PluginOptions, 'spec'>;

export const PluginOptionSchema = Joi.object<PluginOptions>({
  // Direct Usage without redocusaurus preset
  id: Joi.string(),
  debug: Joi.boolean().default(DEFAULT_OPTIONS.debug),
  config: Joi.any().optional(),
  themeId: Joi.string().optional(),

  // Basic
  spec: Joi.string(),
  url: Joi.string().uri({ allowRelative: true }).optional(),
  route: Joi.string().uri({ relativeOnly: true }).optional(),
  layout: Joi.any().default(DEFAULT_OPTIONS.layout),
});
