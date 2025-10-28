const InteractiveElementsQuery =
    "[href],input,button,[role='button'],select,[tabindex]:not([tabindex='-1'])";

/**
 * Whether a pointer event is targeting the element itself or one of its children.
 *
 * @param event The pointer event to check.
 * @returns Whether the event is targeting the element or one of its children.
 */
export function isEventTargetingListener(event?: Pick<Event, "target" | "currentTarget">): boolean {
    const { target: triggerElement, currentTarget: listenerTarget } = event ?? {};

    if (!triggerElement || !listenerTarget) {
        return false;
    }

    if (!(triggerElement instanceof HTMLElement) || !(listenerTarget instanceof HTMLElement)) {
        return false;
    }

    if (triggerElement === listenerTarget) {
        return false;
    }

    return !!(
        triggerElement.matches(InteractiveElementsQuery) ||
        triggerElement.parentElement?.matches(InteractiveElementsQuery)
    );
}
