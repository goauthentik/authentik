/**
 * @file Utility: Traverse shadow roots until the current active element is found.
 */

export function getDeepActiveElement(root: Document | ShadowRoot = document) {
    let active = root.activeElement;
    while (active && active.shadowRoot && active.shadowRoot.activeElement) {
        active = active.shadowRoot.activeElement;
    }
    return active instanceof HTMLElement ? active : null;
}
