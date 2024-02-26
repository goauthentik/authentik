import { CSSResult, unsafeCSS } from "lit";

export const ensureCSSStyleSheet = (css: string | CSSStyleSheet | CSSResult): CSSStyleSheet =>
    typeof css === "string"
        ? (unsafeCSS(css).styleSheet as CSSStyleSheet)
        : css instanceof CSSResult
          ? (css.styleSheet as CSSStyleSheet)
          : css;
