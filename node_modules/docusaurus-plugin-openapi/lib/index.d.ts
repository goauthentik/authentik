import type { LoadContext, Plugin } from "@docusaurus/types";
import type { PluginOptions, LoadedContent } from "./types";
export default function pluginOpenAPI(context: LoadContext, options: PluginOptions): Plugin<LoadedContent>;
export { validateOptions } from "./options";
