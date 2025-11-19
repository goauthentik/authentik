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

/**
 * Recursively renders a collection of sidebar entries.
 */
export function renderSidebarItems(entries: readonly SidebarEntry[]) {
    return repeat(entries, ([path, label]) => path || label, renderSidebarItem);
}

export const createAdminSidebarEntries = (): readonly SidebarEntry[] => [
    [
        null,
        msg("Dashboards", { id: "sidebar.category.dashboards" }),
        { "?expanded": true },
        [
            ["/administration/overview", msg("Overview", { id: "sidebar.item.overview" })],
            [
                "/administration/dashboard/users",
                msg("User Statistics", { id: "sidebar.item.user-statistics" }),
            ],
            [
                "/administration/system-tasks",
                msg("System Tasks", { id: "sidebar.item.system-tasks" }),
            ],
        ],
    ],
    [
        null,
        msg("Applications", { id: "sidebar.category.applications" }),
        null,
        [
            [
                "/core/applications",
                msg("Applications", { id: "sidebar.item.applications" }),
                [`^/core/applications/(?<slug>${SLUG_REGEX})$`],
            ],
            [
                "/core/providers",
                msg("Providers", { id: "sidebar.item.providers" }),
                [`^/core/providers/(?<id>${ID_REGEX})$`],
            ],
            ["/outpost/outposts", msg("Outposts", { id: "sidebar.item.outposts" })],
        ],
    ],
    [
        null,
        msg("Events", { id: "sidebar.category.events" }),
        null,
        [
            ["/events/log", msg("Logs"), [`^/events/log/(?<id>${UUID_REGEX})$`]],
            ["/events/rules", msg("Notification Rules", { id: "sidebar.item.system-tasks" })],
            [
                "/events/transports",
                msg("Notification Transports", { id: "sidebar.item.notification-transports" }),
            ],
        ],
    ],
    [
        null,
        msg("Customization", { id: "sidebar.category.customization" }),
        null,
        [
            ["/policy/policies", msg("Policies", { id: "sidebar.item.policies" })],
            [
                "/core/property-mappings",
                msg("Property Mappings", { id: "sidebar.item.property-mappings" }),
            ],
            ["/blueprints/instances", msg("Blueprints", { id: "sidebar.item.blueprints" })],
            [
                "/policy/reputation",
                msg("Reputation scores", { id: "sidebar.item.reputation-scores" }),
            ],
        ],
    ],
    [
        null,
        msg("Flows and Stages", { id: "sidebar.category.flows-and-stages" }),
        null,
        [
            ["/flow/flows", msg("Flows"), [`^/flow/flows/(?<slug>${SLUG_REGEX})$`]],
            ["/flow/stages", msg("Stages", { id: "sidebar.item.stages" })],
            ["/flow/stages/prompts", msg("Prompts", { id: "sidebar.item.prompts" })],
        ],
    ],
    [
        null,
        msg("Directory", { id: "sidebar.category.directory" }),
        null,
        [
            [
                "/identity/users",
                msg("Users", { id: "sidebar.item.users" }),
                [`^/identity/users/(?<id>${ID_REGEX})$`],
            ],
            [
                "/identity/groups",
                msg("Groups", { id: "sidebar.item.groups" }),
                [`^/identity/groups/(?<id>${UUID_REGEX})$`],
            ],
            [
                "/identity/roles",
                msg("Roles", { id: "sidebar.item.roles" }),
                [`^/identity/roles/(?<id>${UUID_REGEX})$`],
            ],
            [
                "/identity/initial-permissions",
                msg("Initial Permissions", { id: "sidebar.item.initial-permissions" }),
                [`^/identity/initial-permissions/(?<id>${ID_REGEX})$`],
            ],
            [
                "/core/sources",
                msg("Federation and Social login", {
                    id: "sidebar.item.federation-and-social-login",
                }),
                [`^/core/sources/(?<slug>${SLUG_REGEX})$`],
            ],
            [
                "/core/tokens",
                msg("Tokens and App passwords", { id: "sidebar.item.tokens-and-app-passwords" }),
            ],
            ["/flow/stages/invitations", msg("Invitations", { id: "sidebar.item.invitations" })],
        ],
    ],
    [
        null,
        msg("System", { id: "sidebar.category.system" }),
        null,
        [
            ["/core/brands", msg("Brands", { id: "sidebar.item.brands" })],
            ["/crypto/certificates", msg("Certificates", { id: "sidebar.item.certificates" })],
            [
                "/outpost/integrations",
                msg("Outpost Integrations", { id: "sidebar.item.outpost-integrations" }),
            ],
            ["/admin/settings", msg("Settings", { id: "sidebar.item.settings" })],
        ],
    ],
];

export const createAdminSidebarEnterpriseEntries = (): readonly SidebarEntry[] => [
    [
        null,
        msg("Enterprise", { id: "sidebar.category.enterprise" }),
        null,
        [
            [
                "/enterprise/licenses",
                msg("Licenses", {
                    id: "sidebar.item.licenses",
                }),
                null,
            ],
        ],
    ],
];
