const isStyledVisible = ({ visibility, display }: CSSStyleDeclaration) =>
    visibility !== "hidden" && display !== "none";

const isDisplayContents = ({ display }: CSSStyleDeclaration) => display === "contents";

function computedStyleIsVisible(element: HTMLElement) {
    const computedStyle = window.getComputedStyle(element);
    return (
        isStyledVisible(computedStyle) &&
        (isDisplayContents(computedStyle) ||
            Boolean(element.offsetWidth || element.offsetHeight || element.getClientRects().length))
    );
}

export function isVisible(element: HTMLElement) {
    return (
        element &&
        element.isConnected &&
        isStyledVisible(element.style) &&
        computedStyleIsVisible(element)
    );
}
