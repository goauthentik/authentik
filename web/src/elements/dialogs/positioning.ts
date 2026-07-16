export const AnchorPositionSupported: boolean =
    CSS.supports("position-anchor", "--x") && CSS.supports("top", "anchor(bottom)");

/**
 * Whether the browser supports the `anchor-size()` function for sizing an element
 * against its anchor (e.g. `width: anchor-size(width)`).
 *
 * @remarks
 * This is a *separate* capability from {@link AnchorPositionSupported}: Firefox
 * (through at least 152) ships `position-anchor` and `anchor()` but not
 * `anchor-size()`, so a consumer that sizes against its anchor must check this too
 * or the sizing declaration is silently dropped.
 */
export const AnchorSizeSupported: boolean = CSS.supports("width", "anchor-size(width)");
