/**
 * @file Notification drawer utilities.
 */

import "#elements/notifications/APIDrawer";
import "#elements/notifications/NotificationDrawer";

import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";

import { html } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { guard } from "lit/directives/guard.js";

/**
 * The state of the interface drawers.
 *
 * @remarks
 * These values are stored together to avoid awkward rendering states during
 * initialization or rapid toggling.
 */
export interface DrawerState {
    /** Whether the notification drawer is open. */
    notifications: boolean;
    /** Whether the API drawer is open. */
    api: boolean;
}

/**
 * Renders the notification and API drawers based on the provided state.
 *
 * @param drawers The state of the drawers.
 * @returns The rendered drawer panels.
 */
export function renderNotificationDrawerPanel({ notifications, api }: DrawerState) {
    return guard([notifications, api], () => {
        const openDrawerCount = (notifications ? 1 : 0) + (api ? 1 : 0);

        return html`<div
            class=${classMap({
                "pf-c-drawer__panel": true,
                "pf-m-width-33": openDrawerCount === 1,
                "pf-m-width-66": openDrawerCount === 2,
                "pf-u-display-none": openDrawerCount === 0,
            })}
        >
            <ak-api-drawer class="pf-c-drawer__panel_content" ?hidden=${!api}></ak-api-drawer>
            <ak-notification-drawer
                class="pf-c-drawer__panel_content"
                ?hidden=${!notifications}
            ></ak-notification-drawer>
        </div>`;
    });
}

/**
 * Persists the drawer state to the URL parameters.
 */
export function persistDrawerParams(drawers: DrawerState) {
    updateURLParams({
        "drawer-notification": drawers.notifications,
        "drawer-api": drawers.api,
    });
}

/**
 * Reads the drawer state from the URL parameters.
 */
export function readDrawerParams(): DrawerState {
    return {
        notifications: getURLParam("drawer-notification", false),
        api: getURLParam("drawer-api", false),
    };
}
