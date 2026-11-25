/**
 * @file Notification and API drawer panel.
 */

import "#components/notifications/APIDrawer";
import "#components/notifications/NotificationDrawer";
import type { DrawerState } from "#components/notifications/utils";

import { html } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { guard } from "lit/directives/guard.js";

/**
 * Renders the notification and API drawers based on the provided state.
 *
 * @param drawers The state of the drawers.
 *
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
