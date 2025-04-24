import { CSSResult, unsafeCSS } from "lit";

const supportsAdoptingStyleSheets: boolean =
    window.ShadowRoot &&
    (window.ShadyCSS === undefined || window.ShadyCSS.nativeShadow) &&
    "adoptedStyleSheets" in Document.prototype &&
    "replace" in CSSStyleSheet.prototype;

function stringToStylesheet(css: string) {
    if (supportsAdoptingStyleSheets) {
        const sheet = unsafeCSS(css).styleSheet;
        if (sheet === undefined) {
            throw new Error(
                `CSS processing error: undefined stylesheet from string.  Source: ${css}`,
            );
        }
        return sheet;
    }

    const sheet = new CSSStyleSheet();
    sheet.replaceSync(css);
    return sheet;
}

function cssResultToStylesheet(css: CSSResult) {
    const sheet = css.styleSheet;
    return sheet ? sheet : stringToStylesheet(css.toString());
}

export const ensureCSSStyleSheet = (css: string | CSSStyleSheet | CSSResult): CSSStyleSheet =>
    css instanceof CSSResult
        ? cssResultToStylesheet(css)
        : typeof css === "string"
          ? stringToStylesheet(css)
          : css;
