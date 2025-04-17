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

declare module "@docusaurus/plugin-content-docs-types" {
    export * from "@docusaurus/plugin-content-docs";
    export * from "@docusaurus/plugin-content-docs/src/types.ts";
    export * from "@docusaurus/plugin-content-docs/src/sidebars/types.ts";
}

declare module "@docusaurus/plugin-content-docs/src/sidebars/types" {
    export * from "@docusaurus/plugin-content-docs/src/sidebars/types.ts";
}
