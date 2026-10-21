import { toAdminInterface } from "#elements/router/core/interfaces";
import { SidebarAttributes, SidebarEntry } from "#elements/sidebar/utils";

import { msg } from "@lit/localize";

export const ENTERPRISE_PATH = "/enterprise/licenses";

export type SidebarLicenseFlags = { licensed: boolean; canEnterprise: boolean };

const isEnterpriseEntry = (attr: SidebarAttributes | undefined) =>
    attr !== null && !Array.isArray(attr) && typeof attr === "object" && attr.enterprise;

/**
 * Removes enterprise entries entirely if enterprise capability is not present, or marks them "as
 * enterprise" if they are but the product is unlicensed.
 */
export function resolveSidebarEntries(
    entries: readonly SidebarEntry[],
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

                // A feature's details are overridden with "Buy a license" messages if the instance
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

// prettier-ignore
export const initAdminSidebarEntries = (): readonly SidebarEntry[] => [
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
export const initAdminSidebarEnterpriseEntries = (): readonly SidebarEntry[] => [
    [null, msg("Enterprise"), { key: "enterprise" }, [
        ["/enterprise/licenses", msg("Licenses"), null]
    ],
]];

export function createAdminSidebarEntries(needsEnterprise: boolean) {
    const entries = needsEnterprise
        ? [...initAdminSidebarEntries(), ...initAdminSidebarEnterpriseEntries()]
        : initAdminSidebarEntries();

    return entries;
}
