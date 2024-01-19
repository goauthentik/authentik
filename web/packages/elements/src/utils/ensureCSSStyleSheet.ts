import { CSSResult, unsafeCSS } from "lit";

/* Converts a variety of unknown inbound CSS types to a singular type consumable by most browsers.
   This uses Lit's `unsafeCSS` function; do not use this function with any CSS you don't already
   trust well.
*/

export const ensureCSSStyleSheet = (css: string | CSSStyleSheet | CSSResult): CSSStyleSheet =>
    typeof css === "string"
        ? (unsafeCSS(css).styleSheet as CSSStyleSheet)
        : css instanceof CSSResult
        ? (css.styleSheet as CSSStyleSheet)
        : css;
