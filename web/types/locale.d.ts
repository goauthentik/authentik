/**
 * This module is used to satisfy imports from `#locales/*` which have either
 * not yet been generated, or are missing.
 *
 * ```sh
 * npm run build:locales
 * ```
 */

declare module "#locales/*" {
    /**
     * If you see this, try running `npm run build:locales` to generate locale files.
     */
    type MissingLocale = symbol & { readonly __brand?: never };

    const missingLocale: MissingLocale;
    export const templates: MissingLocale;
}
