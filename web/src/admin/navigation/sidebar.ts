import { toAdminInterface } from "#elements/router/core/interfaces";
import { SidebarItemProperties } from "#elements/sidebar/SidebarItem";
import { LitPropertyRecord } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";
import { repeat } from "lit/directives/repeat.js";

export const ENTERPRISE_PATH = "/enterprise/licenses";

export type SidebarAttributes =
    | LitPropertyRecord<SidebarItemProperties & { enterprise?: boolean }>
    | string[]
    | null;

// A `string[]` in the attributes slot lists the route names that keep the entry active.
export type SidebarEntry = [
    path: string | null,
    label: string,
    attributes?: SidebarAttributes,
    children?: SidebarEntry[],
];

export type RouteNameResolver = (path: string) => string | null;

export type SidebarLicenseFlags = { licensed: boolean; canEnterprise: boolean };

const isEnterpriseEntry = (attr: SidebarAttributes | undefined) =>
    attr !== null && !Array.isArray(attr) && typeof attr === "object" && attr.enterprise;

/**
 * Removes enterprise entries entirely if enterprise capability is not present, or marks them "as
 * enterprise" if they are but the product is unlicensed.
 */
export function resolveSidebarEntries(
    entries: SidebarEntry[],
    { licensed, canEnterprise }: SidebarLicenseFlags,
): SidebarEntry[] {
    return (
        entries
            // A feature is always visible if it's not enterprise-only, or if the instance
            // canEnterprise
            .filter(
                ([_path, _label, attributes, _children]) =>
                    !isEnterpriseEntry(attributes) || canEnterprise,
            )

            .map(([path, label, attributes, children]) => {
                const isEnterprise = isEnterpriseEntry(attributes);

                // A feature's details are overriden with "Buy a license" messages if the instance
                // canEnterprise, but the instance is not licensed.
                if (!licensed && isEnterprise) {
                    attributes = {
                        ...attributes,
                        pathOverride: toAdminInterface(ENTERPRISE_PATH),
                        notice: msg("Enterprise only", {
                            id: "sidebar.notice.enterprise-only",
                        }),
                    };
                }

                return children
                    ? [
                          path,
                          label,
                          attributes,
                          resolveSidebarEntries(children, { licensed, canEnterprise }),
                      ]
                    : [path, label, attributes];
            })
    );
}

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
    [null, msg("Dashboards"), { key: "dashboards", "?expanded": true }, [
        ["/administration/overview", msg("Overview")],
        ["/administration/dashboard/users", msg("User Statistics")],
        ["/administration/system-tasks", msg("System Tasks"), ["system-tasks"]]]
    ],
    [null, msg("Applications"), { key: "applications" }, [
        ["/core/applications", msg("Applications"), ["application-view"]],
        ["/core/providers", msg("Providers"), ["provider-view"]],
        ["/outpost/outposts", msg("Outposts"), ["outpost-view"]],
        ["/requests/rules", msg("Request Rules"), {enterprise:true}],
        ["/requests/access-requests", msg("Access Requests"), {enterprise:true}],]
    ],
    [null, msg("Endpoint Devices"), { key: "endpoint-devices" }, [
        ["/endpoints/devices", msg("Devices"), ["device-view"]],
        ["/endpoints/groups", msg("Device access groups")],
        ["/endpoints/connectors", msg("Connectors"), ["connector-view"]],
    ]],
    [null, msg("Events"), { key: "events" }, [
        ["/events/log", msg("Logs"), ["event-view"]],
        ["/events/rules", msg("Notification Rules")],
        ["/events/transports", msg("Notification Transports")],
        ["/events/lifecycle-rules", msg("Lifecycle Rules"), {enterprise:true}],
        ["/events/lifecycle-reviews", msg("Reviews"), {enterprise:true}],
        ["/events/offboardings", msg("Offboardings"), {enterprise:true}],
        ["/events/exports", msg("Data Exports"), {enterprise:true}]]
    ],
    [null, msg("Customization"), { key: "customization" }, [
        ["/policy/policies", msg("Policies")],
        ["/core/property-mappings", msg("Property Mappings")],
        ["/blueprints/instances", msg("Blueprints")],
        ["/files", msg("Files")],
        ["/policy/reputation", msg("Reputation scores")]],
    ],
    [null, msg("Flows and Stages"), { key: "flows-stages" }, [
        ["/flow/flows", msg("Flows"), ["flow-view"]],
        ["/flow/stages", msg("Stages")],
        ["/flow/stages/prompts", msg("Prompts")]]
    ],
    [null, msg("Directory"), { key: "directory" }, [
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
    [null, msg("System"), { key: "system" }, [
        ["/core/brands", msg("Brands")],
        ["/crypto/certificates", msg("Certificates")],
        ["/outpost/integrations", msg("Outpost Integrations")],
        ["/admin/settings", msg("Settings")]]
    ],
];

// prettier-ignore
export const createAdminSidebarEnterpriseEntries = (): readonly SidebarEntry[] => [
    [null, msg("Enterprise"), { key: "enterprise" }, [
        ["/enterprise/licenses", msg("Licenses"), null]
    ],
]];
