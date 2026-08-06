import { isFirefox } from "#elements/utils/useragent";

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
export const AnchorSizeSupported: boolean =
    CSS.supports("width", "anchor-size(width)") && !isFirefox();

/**
 * Tallest an anchored popover may grow, as a fraction of the viewport.
 */
const MAX_POPOVER_VIEWPORT_RATIO = 0.4;

/**
 * Breathing room kept between an anchored popover and the edge of its boundary.
 */
const BOUNDARY_INSET = 8;

/**
 * Shortest popover worth rendering. Inside a boundary too small for even this, the popover
 * overhangs rather than collapsing into an unusable sliver.
 */
const MIN_POPOVER_HEIGHT = 128;

/**
 * Walk the flattened (composed) tree upward from `node`, crossing shadow boundaries and
 * slots.
 */
export function* composedAncestors(node: Node): Generator<HTMLElement> {
    const composedParent = (current: Node): Node | null => {
        const slot = (current as Element).assignedSlot;
        if (slot) return slot;

        const parent = current.parentNode;
        return parent instanceof ShadowRoot ? parent.host : parent;
    };

    for (let current = composedParent(node); current; current = composedParent(current)) {
        if (current instanceof HTMLElement) yield current;
    }
}

function scrollableY(element: HTMLElement): boolean {
    const { overflowY } = getComputedStyle(element);

    return overflowY === "auto" || overflowY === "scroll" || overflowY === "overlay";
}

/**
 * The nearest vertically scrollable ancestor of `node`, crossing shadow boundaries.
 */
export function findScrollableAncestor(node: Node): HTMLElement | null {
    for (const ancestor of composedAncestors(node)) {
        if (scrollableY(ancestor) && ancestor.scrollHeight > ancestor.clientHeight) {
            return ancestor;
        }
    }

    return null;
}

/**
 * The vertical band an anchored popover has to stay within: the dialog containing its
 * anchor, or the viewport when the anchor isn't in one.
 *
 * @remarks
 * A popover renders in the top layer, positioned against the viewport, so nothing clips it
 * to the dialog it belongs to — without this it overhangs the dialog's edges and paints
 * over the backdrop.
 */
export function popoverBoundaryBand(anchor: Node): { top: number; bottom: number } {
    const viewportHeight = window.innerHeight;

    for (const ancestor of composedAncestors(anchor)) {
        if (!(ancestor instanceof HTMLDialogElement)) continue;

        const rect = ancestor.getBoundingClientRect();

        return {
            top: Math.max(0, rect.top),
            bottom: Math.min(viewportHeight, rect.bottom),
        };
    }

    return { top: 0, bottom: viewportHeight };
}

export interface AnchoredPopoverPlacementOptions {
    /**
     * Size the popover to its anchor's width. Menus that belong to a text input want this;
     * free-standing menus size themselves.
     */
    matchAnchorWidth?: boolean;
}

/**
 * Place a top-layer popover against its anchor: below by default, flipped above when the
 * roomier side is up, and never taller than the space its boundary leaves it.
 *
 * @returns Whether the popover was placed above its anchor.
 */
export function placeAnchoredPopover(
    anchor: HTMLElement,
    popover: HTMLElement,
    { matchAnchorWidth }: AnchoredPopoverPlacementOptions = {},
): boolean {
    const rect = anchor.getBoundingClientRect();
    const bounds = popoverBoundaryBand(anchor);

    const ceiling = Math.round(window.innerHeight * MAX_POPOVER_VIEWPORT_RATIO);
    const spaceBelow = bounds.bottom - rect.bottom - BOUNDARY_INSET;
    const spaceAbove = rect.top - bounds.top - BOUNDARY_INSET;

    // `scrollHeight` is the popover's unconstrained content height, so this flips only when
    // the content genuinely doesn't fit below, not on every long list.
    const desired = Math.min(popover.scrollHeight || ceiling, ceiling);
    const flipUp = spaceBelow < desired && spaceAbove > spaceBelow;
    const available = Math.max(flipUp ? spaceAbove : spaceBelow, MIN_POPOVER_HEIGHT);

    popover.style.position = "fixed";
    popover.style.left = `${Math.round(rect.left)}px`;
    popover.style.maxHeight = `${Math.round(Math.min(ceiling, available))}px`;

    if (matchAnchorWidth) {
        popover.style.width = `${Math.round(rect.width)}px`;
    }

    if (flipUp) {
        popover.style.top = "auto";
        popover.style.bottom = `${Math.round(window.innerHeight - rect.top)}px`;
    } else {
        popover.style.bottom = "auto";
        popover.style.top = `${Math.round(rect.bottom)}px`;
    }

    return flipUp;
}
