/**
 * @file Utility: Find the nearest sibling (before, after, or both) that matches a selector;
 */

export function findPreviousSibling(element: HTMLElement, selector: string) {
    let sibling = element.previousElementSibling;
    while (sibling) {
        if (sibling.matches(selector)) {
            return sibling;
        }
        sibling = sibling.previousElementSibling;
    }
    return null;
}

export function findNextSibling(element: HTMLElement, selector: string) {
    let sibling = element.nextElementSibling;
    while (sibling) {
        if (sibling.matches(selector)) {
            return sibling;
        }
        sibling = sibling.nextElementSibling;
    }
    return null;
}

// Alternates between the two to find the "nearest";
export function findNearestSibling(element: HTMLElement, selector: string) {
    let prev = element.previousElementSibling;
    let next = element.nextElementSibling;
    while (prev || next) {
        if (prev?.matches(selector)) {
            return prev;
        }
        if (next?.matches(selector)) {
            return next;
        }
        prev = prev?.previousElementSibling ?? null;
        next = next?.nextElementSibling ?? null;
    }
    return null;
}
