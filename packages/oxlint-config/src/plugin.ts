/**
 * @file The bundled authentik oxlint JS plugin. A single plugin (oxlint requires unique plugin
 *   names) exposing all of authentik's custom rules under the `goauthentik/` namespace.
 */

import { consolePaddingRule } from "./console-padding-plugin.js";
import { multilineStatementPaddingRule } from "./multiline-statement-plugin.js";
import { paddingRule } from "./padding-plugin.js";
import type { Plugin } from "./plugin-types.js";

const authentikPlugin: Plugin = {
    meta: { name: "goauthentik" },
    rules: {
        "padding-lines": paddingRule,
        "console-padding": consolePaddingRule,
        "multiline-statement-padding": multilineStatementPaddingRule,
    },
};

export default authentikPlugin;
