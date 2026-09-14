/**
 * @file Pure path helpers for path-routed tabs.
 *
 * A tab panel is a slotted child named `page-<segment>`; its URL is the tab
 * group's mount path plus that segment (`/if/user/settings` + `sessions` →
 * `/if/user/settings/sessions`). These functions map between the two and pick
 * the active tab from a location. No DOM, no globals — unit-testable in Node.
 */

/**
 * The `slot` prefix every tab panel carries. The URL segment is the slot name
 * with this removed.
 */
export const SLOT_PREFIX = "page-";

export const slotToSegment = (slot: string): string => slot.slice(SLOT_PREFIX.length);
export const segmentToSlot = (segment: string): string => `${SLOT_PREFIX}${segment}`;

/**
 * The active tab slot for a location, or `null` when the group has no tabs.
 *
 * The first tab is the default: the bare base (and any path outside the group's
 * subtree) resolves to it. A path whose first segment past the base names a
 * known tab selects that tab; an unknown segment falls back to the first.
 *
 * @param base The group's mount path, e.g. `/if/user/settings`.
 * @param pathname The current `location.pathname`.
 * @param slots The group's slot names, in tab order.
 */
export function activeSlotForPath(
    base: string,
    pathname: string,
    slots: readonly string[],
): string | null {
    const first = slots[0] ?? null;
    const normalizedBase = base.replace(/\/+$/, "");

    if (pathname.startsWith(`${normalizedBase}/`)) {
        const [segment] = pathname
            .slice(normalizedBase.length + 1)
            .split("/")
            .filter(Boolean);

        if (segment) {
            const slot = segmentToSlot(segment);

            if (slots.includes(slot)) return slot;
        }
    }

    return first;
}

/**
 * The URL a tab links to: the bare `base` for the first (default) tab,
 * `base/segment` otherwise. Keeping the default at the bare base mirrors the
 * legacy behavior of omitting the first tab's parameter.
 *
 * @param base The group's mount path.
 * @param slotName The tab's slot name.
 * @param firstSlot The group's first slot, the default tab.
 */
export function tabHref(base: string, slotName: string, firstSlot: string | null): string {
    const normalizedBase = base.replace(/\/+$/, "");

    if (slotName === firstSlot) return normalizedBase;

    return `${normalizedBase}/${slotToSegment(slotName)}`;
}
