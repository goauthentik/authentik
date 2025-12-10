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
// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference types="@docusaurus/plugin-content-docs" />
/// <reference types="@docusaurus/theme-classic" />
import type { PropDocContent as BasePropDocContent } from "@docusaurus/plugin-content-docs";
import type { DocContextValue as BaseDocContextValue } from "@docusaurus/plugin-content-docs/client";

declare global {
    export interface APIDocFrontMatter {
        readonly info_path?: string;
        readonly api?: string;
        readonly schema?: boolean;
        readonly sample?: unknown;
    }

    export interface PropDocContent extends BasePropDocContent {
        readonly api?: string;
        frontMatter: APIDocFrontMatter & BasePropDocContent["frontMatter"];
    }

    export interface DocContextValue extends BaseDocContextValue {
        frontMatter: APIDocFrontMatter & BasePropDocContent["frontMatter"];
    }
}
