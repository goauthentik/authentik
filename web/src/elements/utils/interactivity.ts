export function isInteractiveElement(target: Element | null | undefined): target is HTMLElement {
    if (!target || !(target instanceof HTMLElement)) {
        return false;
    }

    if (target.hasAttribute("disabled") || target.inert) {
        return false;
    }

    const { tabIndex } = target;

    // Despite our type definitions, this method isn't available in all browsers,
    // so we fallback to assuming the element is visible.
    const visible = target.checkVisibility?.() ?? true;

    return (
        visible &&
        (tabIndex === 0 ||
            tabIndex === -1 ||
            target.matches("button, [role='button'], a[href], input, select, textarea"))
    );
}
