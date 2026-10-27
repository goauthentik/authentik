import { SidebarEntry } from "#elements/sidebar/utils";

import { msg } from "@lit/localize";

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
