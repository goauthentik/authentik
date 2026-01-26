import type { UIPermissions } from "./uiPermissions.js";

import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "#elements/router/Route";
import { SidebarItemProperties } from "#elements/sidebar/SidebarItem";
import { LitPropertyRecord } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";
import { repeat } from "lit/directives/repeat.js";

// The second attribute type is of string[] to help with the 'activeWhen' control, which was
// commonplace and singular enough to merit its own handler.
export type SidebarEntry = [
    path: string | null,
    label: string,
    attributes?: LitPropertyRecord<SidebarItemProperties> | string[] | null,
    children?: SidebarEntry[],
];

/**
 * Recursively renders a collection of sidebar entries.
 */
export function renderSidebarItems(entries: readonly SidebarEntry[]) {
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    return repeat(entries, ([path, label]) => path || label, renderSidebarItem);
}

/**
 * Recursively renders a sidebar entry.
 */
export function renderSidebarItem([
    path,
    label,
    attributes,
    children,
]: SidebarEntry): TemplateResult {
    const properties = Array.isArray(attributes)
        ? { ".activeWhen": attributes }
        : (attributes ?? {});

    if (path) {
        properties.path = path;
    }

    return html`<ak-sidebar-item
        exportparts="list-item, link"
        label=${ifDefined(label)}
        ${spread(properties)}
    >
        ${children ? renderSidebarItems(children) : nothing}
    </ak-sidebar-item>`;
}

function filterSidebarByPermissions(
    entries: readonly SidebarEntry[],
    permissions: UIPermissions,
): SidebarEntry[] {
    const filtered: SidebarEntry[] = [];

    for (const entry of entries) {
        const [path, label, attributes, children] = entry;

        const filteredChildren = children
            ? filterSidebarByPermissions(children, permissions)
            : null;

        let shouldShow = true;

        if (path) {
            if (path === "/administration/overview")
                shouldShow = permissions.can_view_admin_overview;
            else if (path === "/administration/dashboard/users")
                shouldShow = permissions.can_view_users;
            else if (path === "/administration/system-tasks")
                shouldShow = permissions.can_view_system_tasks;
            else if (path === "/core/applications") shouldShow = permissions.can_view_applications;
            else if (path === "/core/providers") shouldShow = permissions.can_view_providers;
            else if (path === "/outpost/outposts") shouldShow = permissions.can_view_outposts;
            else if (path === "/endpoints/devices") shouldShow = permissions.can_view_devices;
            else if (path === "/endpoints/groups") shouldShow = permissions.can_view_device_groups;
            else if (path === "/endpoints/connectors") shouldShow = permissions.can_view_connectors;
            else if (path === "/events/log") shouldShow = permissions.can_view_events;
            else if (path === "/events/rules") shouldShow = permissions.can_view_notification_rules;
            else if (path === "/events/transports")
                shouldShow = permissions.can_view_notification_transports;
            else if (path === "/events/exports") shouldShow = permissions.can_view_data_exports;
            else if (path === "/policy/policies") shouldShow = permissions.can_view_policies;
            else if (path === "/core/property-mappings")
                shouldShow = permissions.can_view_property_mappings;
            else if (path === "/blueprints/instances") shouldShow = permissions.can_view_blueprints;
            else if (path === "/files") shouldShow = permissions.can_view_files;
            else if (path === "/policy/reputation") shouldShow = permissions.can_view_reputation;
            else if (path === "/flow/flows") shouldShow = permissions.can_view_flows;
            else if (path === "/flow/stages") shouldShow = permissions.can_view_stages;
            else if (path === "/flow/stages/prompts") shouldShow = permissions.can_view_prompts;
            else if (path === "/identity/users") shouldShow = permissions.can_view_users;
            else if (path === "/identity/groups") shouldShow = permissions.can_view_groups;
            else if (path === "/identity/roles") shouldShow = permissions.can_view_roles;
            else if (path === "/identity/initial-permissions")
                shouldShow = permissions.can_view_initial_permissions;
            else if (path === "/core/sources") shouldShow = permissions.can_view_sources;
            else if (path === "/core/tokens") shouldShow = permissions.can_view_tokens;
            else if (path === "/flow/stages/invitations")
                shouldShow = permissions.can_view_invitations;
            else if (path === "/core/brands") shouldShow = permissions.can_view_brands;
            else if (path === "/crypto/certificates")
                shouldShow = permissions.can_view_certificates;
            else if (path === "/outpost/integrations")
                shouldShow = permissions.can_view_outpost_integrations;
            else if (path === "/admin/settings") shouldShow = permissions.can_view_settings;
            else if (path === "/enterprise/licenses") shouldShow = permissions.can_view_licenses;
        }

        if (!path) {
            if (filteredChildren && filteredChildren.length > 0) {
                filtered.push([path, label, attributes, filteredChildren]);
            }
        } else if (shouldShow) {
            filtered.push([path, label, attributes, filteredChildren || children]);
        }
    }

    return filtered;
}

// prettier-ignore
export const createAdminSidebarEntries = (): readonly SidebarEntry[] => [
    [null, msg("Dashboards"), { "?expanded": true }, [
        ["/administration/overview", msg("Overview")],
        ["/administration/dashboard/users", msg("User Statistics")],
        ["/administration/system-tasks", msg("System Tasks")]]
    ],
    [null, msg("Applications"), null, [
        ["/core/applications", msg("Applications"), [`^/core/applications/(?<slug>${SLUG_REGEX})$`]],
        ["/core/providers", msg("Providers"), [`^/core/providers/(?<id>${ID_REGEX})$`]],
        ["/outpost/outposts", msg("Outposts")]]
    ],
    [null, msg("Endpoint Devices"), null, [
        ["/endpoints/devices", msg("Devices"), [`^/endpoints/devices/(?<uuid>${UUID_REGEX})$`]],
        ["/endpoints/groups", msg("Device access groups")],
        ["/endpoints/connectors", msg("Connectors"), [`^/endpoints/connectors/(?<uuid>${UUID_REGEX})$`]],
    ]],
    [null, msg("Events"), null, [
        ["/events/log", msg("Logs"), [`^/events/log/(?<id>${UUID_REGEX})$`]],
        ["/events/rules", msg("Notification Rules")],
        ["/events/transports", msg("Notification Transports")],
        ["/events/exports", msg("Data Exports"), { enterprise: true }]]
    ],
    [null, msg("Customization"), null, [
        ["/policy/policies", msg("Policies")],
        ["/core/property-mappings", msg("Property Mappings")],
        ["/blueprints/instances", msg("Blueprints")],
        ["/files", msg("Files")],
        ["/policy/reputation", msg("Reputation scores")]],
    ],
    [null, msg("Flows and Stages"), null, [
        ["/flow/flows", msg("Flows"), [`^/flow/flows/(?<slug>${SLUG_REGEX})$`]],
        ["/flow/stages", msg("Stages")],
        ["/flow/stages/prompts", msg("Prompts")]]
    ],
    [null, msg("Directory"), null, [
        ["/identity/users", msg("Users"), [`^/identity/users/(?<id>${ID_REGEX})$`]],
        ["/identity/groups", msg("Groups"), [`^/identity/groups/(?<id>${UUID_REGEX})$`]],
        ["/identity/roles", msg("Roles"), [`^/identity/roles/(?<id>${UUID_REGEX})$`]],
        ["/identity/initial-permissions", msg("Initial Permissions"), [`^/identity/initial-permissions/(?<id>${ID_REGEX})$`]],
        ["/core/sources", msg("Federation and Social login"), [`^/core/sources/(?<slug>${SLUG_REGEX})$`]],
        ["/core/tokens", msg("Tokens and App passwords")],
        ["/flow/stages/invitations", msg("Invitations")]]
    ],
    [null, msg("System"), null, [
        ["/core/brands", msg("Brands")],
        ["/crypto/certificates", msg("Certificates")],
        ["/outpost/integrations", msg("Outpost Integrations")],
        ["/admin/settings", msg("Settings")]]
    ],
]

// prettier-ignore
export const createAdminSidebarEnterpriseEntries = (): readonly SidebarEntry[] => [
    [null, msg("Enterprise"), null, [
        ["/enterprise/licenses", msg("Licenses"), null]
    ],
    ]]

export function createFilteredAdminSidebarEntries(
    permissions: UIPermissions,
): readonly SidebarEntry[] {
    return filterSidebarByPermissions(createAdminSidebarEntries(), permissions);
}
export function createFilteredAdminSidebarEnterpriseEntries(
    permissions: UIPermissions,
): readonly SidebarEntry[] {
    return filterSidebarByPermissions(createAdminSidebarEnterpriseEntries(), permissions);
}
