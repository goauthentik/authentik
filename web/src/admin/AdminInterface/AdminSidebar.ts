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
// The fifth element is an optional required permission string for access control.
export type SidebarEntry = [
    path: string | null,
    label: string,
    attributes?: LitPropertyRecord<SidebarItemProperties> | string[] | null,
    children?: SidebarEntry[],
    requiredPermission?: string,
];

/**
 * Recursively renders a collection of sidebar entries.
 */
export function renderSidebarItems(entries: readonly SidebarEntry[]) {
    // eslint-disable-next-line @typescript-eslint/no-use-before-define
    return repeat(entries, ([path, label]) => path || label, renderSidebarItem);
}

/**
 * Extract a flat map of path prefixes to required permissions from sidebar entries.
 */
export function extractRoutePermissions(
    entries: readonly SidebarEntry[],
): Map<string, string> {
    const permissions = new Map<string, string>();

    function processEntries(items: readonly SidebarEntry[]) {
        for (const [path, , , children, requiredPermission] of items) {
            if (path && requiredPermission) {
                permissions.set(path, requiredPermission);
            }
            if (children) {
                processEntries(children);
            }
        }
    }

    processEntries(entries);
    return permissions;
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

// prettier-ignore
export const createAdminSidebarEntries = (): readonly SidebarEntry[] => [
    [null, msg("Dashboards"), { "?expanded": true }, [
        ["/administration/overview", msg("Overview"), null, undefined, "authentik_rbac.view_system_info"],
        ["/administration/dashboard/users", msg("User Statistics"), null, undefined, "authentik_core.view_user"],
        ["/administration/system-tasks", msg("System Tasks"), null, undefined, "authentik_events.view_systemtask"]]
    ],
    [null, msg("Applications"), null, [
        ["/core/applications", msg("Applications"), [`^/core/applications/(?<slug>${SLUG_REGEX})$`], undefined, "authentik_core.view_application"],
        ["/core/providers", msg("Providers"), [`^/core/providers/(?<id>${ID_REGEX})$`], undefined, "authentik_core.view_provider"],
        ["/outpost/outposts", msg("Outposts"), null, undefined, "authentik_outposts.view_outpost"]]
    ],
    [null, msg("Endpoint Devices"), null, [
        ["/endpoints/devices", msg("Devices"), [`^/endpoints/devices/(?<uuid>${UUID_REGEX})$`], undefined, "authentik_endpoints.view_device"],
        ["/endpoints/groups", msg("Device access groups"), null, undefined, "authentik_endpoints.view_devicegroup"],
        ["/endpoints/connectors", msg("Connectors"), [`^/endpoints/connectors/(?<uuid>${UUID_REGEX})$`], undefined, "authentik_endpoints.view_endpointconnector"],
    ]],
    [null, msg("Events"), null, [
        ["/events/log", msg("Logs"), [`^/events/log/(?<id>${UUID_REGEX})$`], undefined, "authentik_events.view_event"],
        ["/events/rules", msg("Notification Rules"), null, undefined, "authentik_events.view_notificationrule"],
        ["/events/transports", msg("Notification Transports"), null, undefined, "authentik_events.view_notificationtransport"],
        ["/events/exports", msg("Data Exports"), {enterprise:true}, undefined, "authentik_enterprise.view_dataexport"]]
    ],
    [null, msg("Customization"), null, [
        ["/policy/policies", msg("Policies"), null, undefined, "authentik_policies.view_policy"],
        ["/core/property-mappings", msg("Property Mappings"), null, undefined, "authentik_core.view_propertymapping"],
        ["/blueprints/instances", msg("Blueprints"), null, undefined, "authentik_blueprints.view_blueprintinstance"],
        ["/files", msg("Files"), null, undefined, "authentik_rbac.manage_media_files"],
        ["/policy/reputation", msg("Reputation scores"), null, undefined, "authentik_policies_reputation.view_reputation"]],
    ],
    [null, msg("Flows and Stages"), null, [
        ["/flow/flows", msg("Flows"), [`^/flow/flows/(?<slug>${SLUG_REGEX})$`], undefined, "authentik_flows.view_flow"],
        ["/flow/stages", msg("Stages"), null, undefined, "authentik_flows.view_stage"],
        ["/flow/stages/prompts", msg("Prompts"), null, undefined, "authentik_stages_prompt.view_prompt"]]
    ],
    [null, msg("Directory"), null, [
        ["/identity/users", msg("Users"), [`^/identity/users/(?<id>${ID_REGEX})$`], undefined, "authentik_core.view_user"],
        ["/identity/groups", msg("Groups"), [`^/identity/groups/(?<id>${UUID_REGEX})$`], undefined, "authentik_core.view_group"],
        ["/identity/roles", msg("Roles"), [`^/identity/roles/(?<id>${UUID_REGEX})$`], undefined, "authentik_rbac.view_role"],
        ["/identity/initial-permissions", msg("Initial Permissions"), [`^/identity/initial-permissions/(?<id>${ID_REGEX})$`], undefined, "authentik_rbac.view_initialpermissions"],
        ["/core/sources", msg("Federation and Social login"), [`^/core/sources/(?<slug>${SLUG_REGEX})$`], undefined, "authentik_core.view_source"],
        ["/core/tokens", msg("Tokens and App passwords"), null, undefined, "authentik_core.view_token"],
        ["/flow/stages/invitations", msg("Invitations"), null, undefined, "authentik_stages_invitation.view_invitation"]]
    ],
    [null, msg("System"), null, [
        ["/core/brands", msg("Brands"), null, undefined, "authentik_brands.view_brand"],
        ["/crypto/certificates", msg("Certificates"), null, undefined, "authentik_crypto.view_certificatekeypair"],
        ["/outpost/integrations", msg("Outpost Integrations"), null, undefined, "authentik_outposts.view_outpostserviceconnection"],
        ["/admin/settings", msg("Settings"), null, undefined, "authentik_rbac.view_system_settings"]]
    ],
];

// prettier-ignore
export const createAdminSidebarEnterpriseEntries = (): readonly SidebarEntry[] => [
    [null, msg("Enterprise"), null, [
        ["/enterprise/licenses", msg("Licenses"), null, undefined, "authentik_enterprise.view_license"]
    ],
]]
