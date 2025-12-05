import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "#elements/router/Route";
import { LitPropertyRecord } from "#elements/types";

import { SidebarItemProperties } from "#admin/sidebar/SidebarItem";

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
        ["/events/transports", msg("Notification Transports")]]
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
];

// prettier-ignore
export const createAdminSidebarEnterpriseEntries = (): readonly SidebarEntry[] => [
    [null, msg("Enterprise"), null, [
        ["/enterprise/licenses", msg("Licenses"), null]
    ],
]]
