/**
 * @file Utilities for determining interactivity of elements.
 */

const InteractiveElementsQuery = "button, [role='button'], a[href], input, select, textarea";

/**
 * Predicate to determine if an element is interactive, i.e. can receive focus and user input.
 *
 * @param target The element to check.
 * @param immediately Whether to check for immediate interactivity (not considering visibility).
 */
export function isInteractiveElement(
    target: Element | null | undefined,
    immediately = true,
): target is HTMLElement {
    if (!target || !(target instanceof HTMLElement)) {
        return false;
    }

    if (!immediately) {
        return target.matches(InteractiveElementsQuery);
    }

    if (target.hasAttribute("disabled") || target.inert) {
        return false;
    }

    const { tabIndex } = target;

    // Despite our type definitions, this method isn't available in all browsers,
    // so we fallback to assuming the element is visible.
    const visible = target.checkVisibility?.() ?? true;

    return (
        visible && (tabIndex === 0 || tabIndex === -1 || target.matches(InteractiveElementsQuery))
    );
}
