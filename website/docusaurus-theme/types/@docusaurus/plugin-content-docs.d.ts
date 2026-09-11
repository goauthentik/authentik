/**
 * @remarks
 *
 *   Docusaurus uses an unconventional module resolution strategy, which can lead to issues when
 *   using TypeScript. The types in this file are intended to expose less visible types to
 *   TypeScript's project references, allowing for better type checking and autocompletion.
 * @file Supplemental type definitions for Docusaurus.
 */

declare module "@docusaurus/plugin-content-docs/client" {
    export * from "@docusaurus/plugin-content-docs/lib/client/doc.js";
    export * from "@docusaurus/plugin-content-docs/lib/client/docSidebarItemsExpandedState.js";
    export * from "@docusaurus/plugin-content-docs/lib/client/docsUtils.js";

    import { DocFrontMatter as BaseDocFrontMatter } from "@docusaurus/plugin-content-docs";
    import { DocContextValue as BaseDocContextValue } from "@docusaurus/plugin-content-docs/lib/client/doc.js";

    /**
     * @monkeypatch
     */
    export interface DocFrontMatter extends BaseDocFrontMatter {
        beta?: boolean;
        support_level?: string;
        authentik_version?: string;
        authentik_preview: boolean;
        authentik_enterprise: boolean;
    }

    export interface DocContextValue extends BaseDocContextValue {
        /**
         * @monkeypatch
         */
        frontMatter: DocFrontMatter;
    }

    export function useDoc(): DocContextValue;
}
