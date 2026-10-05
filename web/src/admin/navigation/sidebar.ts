import type { SidebarItemProperties } from "#elements/sidebar/SidebarItem";
import type { LitPropertyRecord } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";
import { repeat } from "lit/directives/repeat.js";

// A `string[]` in the attributes slot lists the route names that keep the entry active.
export type SidebarEntry = [
    path: string | null,
    label: string,
    attributes?: LitPropertyRecord<SidebarItemProperties> | string[] | null,
    children?: SidebarEntry[],
];

export type RouteNameResolver = (path: string) => string | null;

/**
 * Recursively renders a collection of sidebar entries.
 */
export function renderSidebarItems(
    entries: readonly SidebarEntry[],
    resolveRouteName: RouteNameResolver,
) {
    return repeat(
        entries,
        ([path, label]) => path || label,
        // eslint-disable-next-line @typescript-eslint/no-use-before-define
        (entry) => renderSidebarItem(entry, resolveRouteName),
    );
}

/**
 * Recursively renders a sidebar entry.
 */
export function renderSidebarItem(
    [path, label, attributes, children]: SidebarEntry,
    resolveRouteName: RouteNameResolver,
): TemplateResult {
    const properties = Array.isArray(attributes)
        ? {
              ".activeWhen": (activePath: string) =>
                  attributes.includes(resolveRouteName(activePath) ?? ""),
          }
        : (attributes ?? {});

    if (path) {
        properties.path = path;
    }

    return html`<ak-sidebar-item
        exportparts="list-item, link"
        label=${ifDefined(label)}
        ${spread(properties)}
    >
        ${children ? renderSidebarItems(children, resolveRouteName) : nothing}
    </ak-sidebar-item>`;
}

/**
 * The label of the entry that lists the given route, e.g. "Providers" for `provider-view`.
 */
export function findSidebarSectionByRoute(
    entries: readonly SidebarEntry[],
    routeName: string | null,
): string | null {
    if (!routeName) return null;

    for (const [, label, attributes, children] of entries) {
        if (Array.isArray(attributes) && attributes.includes(routeName)) return label;

        const childLabel = children ? findSidebarSectionByRoute(children, routeName) : null;

        if (childLabel) return childLabel;
    }

    return null;
}

// prettier-ignore
export const createAdminSidebarEntries = (): readonly SidebarEntry[] => [
    [null, msg("Dashboards"), { key: "dashboards", "?expanded": true, icon: "fas fa-chart-pie"  }, [
        ["/administration/overview", msg("Overview")],
        ["/administration/dashboard/users", msg("User Statistics")],
        ["/administration/system-tasks", msg("System Tasks"), ["system-tasks"]]]
    ],
    [null, msg("Applications"), { key: "applications", icon: "fas fa-th-large" }, [
        ["/core/applications", msg("Applications"), ["application-view"]],
        ["/core/providers", msg("Providers"), ["provider-view"]],
        ["/outpost/outposts", msg("Outposts"), ["outpost-view"]],
        ["/requests/rules", msg("Request Rules"), {enterprise:true}],
        ["/requests/access-requests", msg("Access Requests"), {enterprise:true}],]
    ],
    [null, msg("Endpoint Devices"), { key: "endpoint-devices", icon: "fas fa-desktop" }, [
        ["/endpoints/devices", msg("Devices"), ["device-view"]],
        ["/endpoints/groups", msg("Device access groups")],
        ["/endpoints/connectors", msg("Connectors"), ["connector-view"]],
    ]],
    [null, msg("Events"), { key: "events", icon: "fas fa-bell" }, [
        ["/events/log", msg("Logs"), ["event-view"]],
        ["/events/rules", msg("Notification Rules")],
        ["/events/transports", msg("Notification Transports")],
        ["/events/lifecycle-rules", msg("Lifecycle Rules"), {enterprise:true}],
        ["/events/lifecycle-reviews", msg("Reviews"), {enterprise:true}],
        ["/events/offboardings", msg("Offboardings"), {enterprise:true}],
        ["/events/exports", msg("Data Exports"), {enterprise:true}]]
    ],
    [null, msg("Customization"), { key: "customization", icon: "fas fa-sliders-h" }, [
        ["/policy/policies", msg("Policies")],
        ["/core/property-mappings", msg("Property Mappings")],
        ["/blueprints/instances", msg("Blueprints")],
        ["/files", msg("Files")],
        ["/policy/reputation", msg("Reputation scores")]],
    ],
    [null, msg("Flows and Stages"), { key: "flows-stages", icon: "fas fa-project-diagram" }, [
        ["/flow/flows", msg("Flows"), ["flow-view"]],
        ["/flow/stages", msg("Stages")],
        ["/flow/stages/prompts", msg("Prompts")]]
    ],
    [null, msg("Directory"), { key: "directory", icon: "fas fa-address-book" }, [
        ["/identity/users", msg("Users"), ["user-view"]],
        ["/identity/groups", msg("Groups"), ["group-view"]],
        ["/identity/roles", msg("Roles"), ["role-view"]],
        ["/identity/agents", msg("Agents"), {enterprise:true}],
        ["/identity/object-attributes", msg("Object attributes")],
        ["/identity/initial-permissions", msg("Initial Permissions")],
        ["/core/sources", msg("Federation and Social login"), ["source-view"]],
        ["/core/tokens", msg("Tokens and App passwords")],
        ["/flow/stages/invitations", msg("Invitations")]]
    ],
    [null, msg("System"), { key: "system", icon: "fas fa-cogs" }, [
        ["/core/brands", msg("Brands")],
        ["/crypto/certificates", msg("Certificates")],
        ["/outpost/integrations", msg("Outpost Integrations")],
        ["/admin/settings", msg("Settings")]]
    ],
];

// prettier-ignore
export const createAdminSidebarEnterpriseEntries = (): readonly SidebarEntry[] => [
    [null, msg("Enterprise"), { key: "enterprise", icon: "fas fa-building" }, [
        ["/enterprise/licenses", msg("Licenses"), null]
    ],
]];
