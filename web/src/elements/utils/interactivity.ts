export const InteractiveElementsQuery =
    "[href],input,button,i,[role='button'],select,[tabindex]:not([tabindex='-1'])";

export function isInteractiveElement(
    target: EventTarget | Element | null | undefined,
): target is HTMLElement {
    if (!target) return false;

    if (!(target instanceof HTMLElement)) {
        return false;
    }

    if (target.hasAttribute("disabled") || target.inert) {
        return false;
    }

    // Despite our type definitions, this method isn't available in all browsers,
    // so we fallback to assuming the element is visible.
    const visible = target.checkVisibility?.() ?? true;

    const { tabIndex } = target;

    return (
        visible && (tabIndex === 0 || tabIndex === -1 || target.matches(InteractiveElementsQuery))
    );
}
