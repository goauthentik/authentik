/**
 * @file Scrollbar utilities.
 */

/**
 * @returns The width of the scrollbar in pixels, or 0 if the browser uses overlay scrollbars.
 */
export function measureScrollbarWidth(container: HTMLElement = document.body): number {
    const outer = container.ownerDocument.createElement("div");

    outer.style.overflow = "scroll";
    outer.style.width = "100px";
    outer.style.visibility = "hidden";

    container.appendChild(outer);

    const width = outer.offsetWidth - outer.clientWidth;

    container.removeChild(outer);

    return width;
}

export const ScrollbarClassName = {
    Visible: "ak-m-visible-scrollbars",
    Overlay: "ak-m-overlay-scrollbars",
} as const;

export type ScrollbarClassName = (typeof ScrollbarClassName)[keyof typeof ScrollbarClassName];

/**
 * Applies the appropriate scrollbar class to the given container element
 * based on whether the browser uses visible or overlay scrollbars.
 *
 * @param ownerDocument The document to apply the scrollbar class to.
 */
export function applyScrollbarClass(ownerDocument: Document = document): void {
    const scrollbarWidth = measureScrollbarWidth(ownerDocument.body);

    if (scrollbarWidth) {
        ownerDocument.documentElement.classList.add(ScrollbarClassName.Visible);
        ownerDocument.documentElement.classList.remove(ScrollbarClassName.Overlay);
    } else {
        ownerDocument.documentElement.classList.add(ScrollbarClassName.Overlay);
        ownerDocument.documentElement.classList.remove(ScrollbarClassName.Visible);
    }
}
