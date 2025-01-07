import type { OptionValidationContext } from "@docusaurus/types";
import { Joi } from "@docusaurus/utils-validation";
import type { PluginOptions } from "./types";
export declare const DEFAULT_OPTIONS: Omit<PluginOptions, "id" | "sidebarPath">;
export declare const OptionsSchema: Joi.ObjectSchema<PluginOptions>;
export declare function validateOptions({ validate, options: userOptions, }: OptionValidationContext<PluginOptions, PluginOptions>): PluginOptions;
