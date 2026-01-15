import "#admin/AdminInterface/AdminAccessDenied";

import {
    createAdminSidebarEntries,
    createAdminSidebarEnterpriseEntries,
    extractRoutePermissions,
} from "./AdminSidebar.js";

import { ROUTE_SEPARATOR } from "#common/constants";

import { WithSession } from "#elements/mixins/session";
import { RouterOutlet } from "#elements/router/RouterOutlet";

import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

// Build route permissions map from sidebar entries (single source of truth)
const ROUTE_PERMISSIONS = new Map([
    ...extractRoutePermissions(createAdminSidebarEntries()),
    ...extractRoutePermissions(createAdminSidebarEnterpriseEntries()),
]);

@customElement("ak-admin-router-outlet")
export class AdminRouterOutlet extends WithSession(RouterOutlet) {
    /**
     * Check if the current user has a specific permission.
     */
    private hasPermission(permission: string): boolean {
        const user = this.currentUser;
        if (!user) return false;
        if (user.isSuperuser) return true;
        return user.systemPermissions?.includes(permission) ?? false;
    }

    /**
     * Get the required permission for a given URL path.
     * Matches the longest path prefix that has a permission defined.
     */
    private getRequiredPermission(path: string): string | null {
        // Try exact match first
        if (ROUTE_PERMISSIONS.has(path)) {
            return ROUTE_PERMISSIONS.get(path)!;
        }

        // Try prefix matching (for detail pages like /identity/users/123)
        for (const [routePath, permission] of ROUTE_PERMISSIONS) {
            if (path.startsWith(routePath + "/") || path === routePath) {
                return permission;
            }
        }

        return null;
    }

    render(): TemplateResult | undefined {
        // Get current path
        const activeUrl = window.location.hash.slice(1).split(ROUTE_SEPARATOR)[0];

        // Check if this route requires a permission
        const requiredPermission = this.getRequiredPermission(activeUrl);

        if (requiredPermission && !this.hasPermission(requiredPermission)) {
            return html`<ak-admin-access-denied
                permission=${requiredPermission}
            ></ak-admin-access-denied>`;
        }

        return super.render();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-router-outlet": AdminRouterOutlet;
    }
}
