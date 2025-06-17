/**
 * @file Supplemental type definitions for Docusaurus.
 *
 * @remarks
 *
 * Docusaurus uses an unconventional module resolution strategy, which can lead to
 * issues when using TypeScript.
 *
 * The types in this file are intended to expose less visible types to TypeScript's
 * project references, allowing for better type checking and autocompletion.
 */

declare module "@docusaurus/plugin-content-docs/client" {
    export * from "@docusaurus/plugin-content-docs/lib/client/doc.js";
    export * from "@docusaurus/plugin-content-docs/lib/client/docSidebarItemsExpandedState.js";
    export * from "@docusaurus/plugin-content-docs/lib/client/docsUtils.js";

    import { DocContextValue as BaseDocContextValue } from "@docusaurus/plugin-content-docs/lib/client/doc.js";
    import { DocFrontMatter as BaseDocFrontMatter } from "@docusaurus/plugin-content-docs";

    /**
     * @monkeypatch
     */
    export interface DocFrontMatter extends BaseDocFrontMatter {
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
