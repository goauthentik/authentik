/**
 * @file Common document utilities for reading server-injected metadata and JSON scripts.
 */

/**
 * The names of the `<meta>` tags and `json_script` blocks the server injects into the document.
 *
 * @see {@link authentik/core/templates/base/header_js.html}
 */
export const ServerContextMeta = {
    Brand: "ak-brand",
    Config: "ak-config",
    Locale: "ak-locale",
    VersionFamily: "ak-version-family",
    VersionSubdomain: "ak-version-subdomain",
    Build: "ak-build",
    BaseURL: "ak-base-url",
    BaseURLRel: "ak-base-url-rel",
    FlowLayout: "ak-flow-layout",
    FlowTitle: "ak-flow-title",
    FlowBackground: "ak-flow-background",
} as const satisfies Record<string, string>;

export type ServerContextMeta = (typeof ServerContextMeta)[keyof typeof ServerContextMeta];
