import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "#elements/router/Route";
import { SidebarItemProperties } from "#elements/sidebar/SidebarItem";
import { LitPropertyRecord } from "#elements/types";

import {
    toAdministrationDashboardUsers,
    toAdministrationOverview,
    toAdministrationSystemTasks,
    toAdminSettings,
    toApplications,
    toBlueprintsInstances,
    toBrands,
    toCryptoCertificates,
    toEnterpriseLicenses,
    toEventLogs,
    toEventsRules,
    toEventsTransports,
    toFlows,
    toFlowStages,
    toFlowStagesInvitations,
    toFlowStagesPrompts,
    toIdentityGroups,
    toIdentityInitialPermissions,
    toIdentityRoles,
    toIdentityUsers,
    toOutpostIntegrations,
    toOutposts,
    toPolicyPolicies,
    toPolicyReputation,
    toPropertyMappings,
    toProviders,
    toSources,
    toTokens,
} from "#admin/navigation";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";
import { repeat } from "lit/directives/repeat.js";

// The second attribute type is of string[] to help with the 'activeWhen' control, which was
// commonplace and singular enough to merit its own handler.
type SidebarEntry = [
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

    return html`<ak-sidebar-item label=${ifDefined(label)} ${spread(properties)}>
        ${children ? renderSidebarItems(children) : nothing}
    </ak-sidebar-item>`;
}

/**
 * Recursively renders a collection of sidebar entries.
 */
export function renderSidebarItems(entries: readonly SidebarEntry[]) {
    return repeat(entries, ([path, label]) => path || label, renderSidebarItem);
}

// prettier-ignore
export const AdminSidebarEntries: readonly SidebarEntry[] = [
    [null, msg("Dashboards"), { "?expanded": true }, [
        [toAdministrationOverview() , msg("Overview")],
        [toAdministrationDashboardUsers() , msg("User Statistics")],
        [toAdministrationSystemTasks() , msg("System Tasks")]]
    ],
    [null, msg("Applications"), null, [
        [toApplications(), msg("Applications"), [`^/core/applications/(?<slug>${SLUG_REGEX})$`]],
        [toProviders(), msg("Providers"), [`^/core/providers/(?<id>${ID_REGEX})$`]],
        [toOutposts(), msg("Outposts")]]
    ],
    [null, msg("Events"), null, [
        [toEventLogs(), msg("Logs"), [`^/events/log/(?<id>${UUID_REGEX})$`]],
        [toEventsRules() , msg("Notification Rules")],
        [toEventsTransports() , msg("Notification Transports")]]
    ],
    [null, msg("Customization"), null, [
        [toPolicyPolicies() , msg("Policies")],
        [toPropertyMappings() , msg("Property Mappings")],
        [toBlueprintsInstances() , msg("Blueprints")],
        [toPolicyReputation() , msg("Reputation scores")]]
    ],
    [null, msg("Flows and Stages"), null, [
        [toFlows() , msg("Flows"), [`^/flow/flows/(?<slug>${SLUG_REGEX})$`]],
        [toFlowStages() , msg("Stages")],
        [toFlowStagesPrompts() , msg("Prompts")]]
    ],
    [null, msg("Directory"), null, [
        [toIdentityUsers() , msg("Users"), [`^/identity/users/(?<id>${ID_REGEX})$`]],
        [toIdentityGroups() , msg("Groups"), [`^/identity/groups/(?<id>${UUID_REGEX})$`]],
        [toIdentityRoles() , msg("Roles"), [`^/identity/roles/(?<id>${UUID_REGEX})$`]],
        [toIdentityInitialPermissions() , msg("Initial Permissions"), [`^/identity/initial-permissions/(?<id>${ID_REGEX})$`]],
        [toSources() , msg("Federation and Social login"), [`^/core/sources/(?<slug>${SLUG_REGEX})$`]],
        [toTokens() , msg("Tokens and App passwords")],
        [toFlowStagesInvitations() , msg("Invitations")]]
    ],
    [null, msg("System"), null, [
        [toBrands() , msg("Brands")],
        [toCryptoCertificates() , msg("Certificates")],
        [toOutpostIntegrations() , msg("Outpost Integrations")],
        [toAdminSettings() , msg("Settings")]]
    ],
];

// prettier-ignore
export const AdminSidebarEnterpriseEntries: readonly SidebarEntry[] = [
    [null, msg("Enterprise"), null, [
        [toEnterpriseLicenses(), msg("Licenses"), null]
    ],
]]
