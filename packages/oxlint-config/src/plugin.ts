/**
 * @file The bundled authentik oxlint JS plugin. A single plugin (oxlint requires unique plugin
 *   names) exposing all of authentik's custom rules under the `goauthentik/` namespace.
 */

import { paddingRule } from "./padding-plugin.js";
import type { Plugin } from "./plugin-types.js";

const authentikPlugin: Plugin = {
    meta: { name: "goauthentik" },
    rules: {
        "padding-lines": paddingRule,
    },
};

export default authentikPlugin;
