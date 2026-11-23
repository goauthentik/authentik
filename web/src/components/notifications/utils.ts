/**
 * @file Notification drawer utilities.
 */

import { getSearchParam, updateSearchParams } from "#elements/router/core/search-params";

import { type Notification, type PaginatedNotificationList } from "@goauthentik/api";

/**
 * Creates a PaginatedNotificationList from an iterable of notifications.
 */
export function createPaginatedNotificationListFrom(
    input: Iterable<Notification> = [],
): PaginatedNotificationList {
    const results = Array.from(input);

    return {
        pagination: {
            count: results.length,
            next: 0,
            previous: 0,
            current: 0,
            totalPages: 1,
            startIndex: 0,
            endIndex: 0,
        },
        results,
        autocomplete: [],
    };
}

/**
 * The state of the interface drawers.
 *
 * @remarks
 *   These values are stored together to avoid awkward rendering states during
 *   initialization or rapid toggling.
 */
export interface DrawerState {
    /** Whether the notification drawer is open. */
    notifications: boolean;
    /** Whether the API drawer is open. */
    api: boolean;
}

/**
 * Persists the drawer state to the URL parameters.
 */
export function persistDrawerParams(drawers: DrawerState) {
    updateSearchParams({
        "drawer-notification": drawers.notifications,
        "drawer-api": drawers.api,
    });
}

/**
 * Reads the drawer state from the URL parameters.
 */
export function readDrawerParams(): DrawerState {
    return {
        notifications: getSearchParam("drawer-notification", false),
        api: getSearchParam("drawer-api", false),
    };
}
