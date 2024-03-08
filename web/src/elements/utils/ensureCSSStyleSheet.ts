import { CSSResult, unsafeCSS } from "lit";

export const supportsAdoptingStyleSheets: boolean =
  window.ShadowRoot &&
  (window.ShadyCSS === undefined || window.ShadyCSS.nativeShadow) &&
  'adoptedStyleSheets' in Document.prototype &&
  'replace' in CSSStyleSheet.prototype;


function stringToStyleSheet(css: string) {
    if (supportsAdoptingStyleSheets) {
        const sheet = unsafeCSS(css).styleSheet;
        return sheet as CSSStyleSheet;
    }

    const sheet = new CSSStyleSheet();
    sheet.replaceSync(css);
    return sheet;
}


export const ensureCSSStyleSheet = (css: string | CSSStyleSheet | CSSResult): CSSStyleSheet | CSSResult => {
    if (css instanceof CSSResult) {
        return css;
    }

    if (typeof css === "string") {
        return stringToStyleSheet(css);
    }

    return css;
}
