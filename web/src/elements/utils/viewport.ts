export function findNearestBoxTarget(element?: Element | null): Element {
    if (!element) {
        return document.documentElement;
    }

    if (element.getClientRects().length) {
        return element;
    }

    return findNearestBoxTarget(element.parentElement);
}

export function isInViewport(element: Element): boolean {
    const rect = element.getBoundingClientRect();

    return (
        rect.top < window.innerHeight &&
        rect.bottom > 0 &&
        rect.left < window.innerWidth &&
        rect.right > 0
    );
}
