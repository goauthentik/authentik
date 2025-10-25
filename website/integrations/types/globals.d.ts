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
/// <reference types="@docusaurus/plugin-content-docs" />
/// <reference types="@docusaurus/theme-classic" />
