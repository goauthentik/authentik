import { CSSResult } from "lit";

export const ensureCSSStyleSheet = (css: CSSStyleSheet | CSSResult): CSSStyleSheet =>
    css instanceof CSSResult ? css.styleSheet! : css;
