/**
 * @file ESBuild CSS module type definitions.
 */

declare module "*.css" {
    import { CSSResult } from "lit";

    global {
        /**
         * A branded type representing a CSS file imported by ESBuild.
         *
         * While this is a `string`, this is typed as a {@linkcode CSSResult}
         * to satisfy LitElement's `static styles` property.
         */
        export type CSSModule = CSSResult & { readonly __brand?: string };
    }

    /**
     * The text content of a CSS file imported by ESBuild.
     */
    const css: CSSModule;
    export default css;
}
