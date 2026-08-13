import "#admin/admin-overview/AdminOverviewPage";

import { toUserInterface } from "#elements/router/core/interfaces";
import { navigate } from "#elements/router/core/navigation";
import { Route, type RouteLike } from "#elements/router/core/Route";

import { html } from "lit";

/**
 * The admin interface's default path. The outlet replace-redirects `/` here.
 */
export const DEFAULT_PATH = "/administration/overview";

/**
 * The admin interface route table.
 *
 * Route names are stable identifiers used for Sentry span naming.
 *
 * NOTE: literal sub-routes (e.g. a future "/core/applications/new") MUST be
 * registered before their sibling ":slug"/":id" param route so they are not
 * shadowed; "new" is reserved as a slug.
 */
export const ROUTES: RouteLike[] = [
    // Cross-interface: full-load redirect to the user interface.
    new Route(
        "/library",
        () => {
            navigate(toUserInterface(), { mode: "assign" });
            return html``;
        },
        "library-redirect",
    ),

    new Route(
        "/administration/overview",
        () => html`<ak-admin-overview></ak-admin-overview>`,
        "overview",
    ),
    new Route(
        "/administration/dashboard/users",
        async () => {
            await import("#admin/admin-overview/DashboardUserPage");
            return html`<ak-admin-dashboard-users></ak-admin-dashboard-users>`;
        },
        "dashboard-users",
    ),
    new Route(
        "/administration/system-tasks",
        async () => {
            await import("#admin/admin-overview/SystemTasksPage");
            return html`<ak-system-tasks></ak-system-tasks>`;
        },
        "system-tasks",
    ),

    new Route(
        "/core/providers",
        async () => {
            await import("#admin/providers/ProviderListPage");
            return html`<ak-provider-list></ak-provider-list>`;
        },
        "providers",
    ),
    new Route<{ id: string }>(
        "/core/providers/:id",
        async (args) => {
            await import("#admin/providers/ProviderViewPage");
            return html`<ak-provider-view .providerID=${parseInt(args.id, 10)}></ak-provider-view>`;
        },
        "provider-view",
    ),

    new Route(
        "/core/applications",
        async () => {
            await import("#admin/applications/ApplicationListPage");
            return html`<ak-application-list></ak-application-list>`;
        },
        "applications",
    ),
    new Route<{ slug: string }>(
        "/core/applications/:slug",
        async (args) => {
            await import("#admin/applications/ApplicationViewPage");
            return html`<ak-application-view .applicationSlug=${args.slug}></ak-application-view>`;
        },
        "application-view",
    ),

    new Route(
        "/endpoints/devices",
        async () => {
            await import("#admin/endpoints/devices/DeviceListPage");
            return html`<ak-endpoints-device-list></ak-endpoints-device-list>`;
        },
        "devices",
    ),
    new Route<{ uuid: string }>(
        "/endpoints/devices/:uuid",
        async (args) => {
            await import("#admin/endpoints/devices/DeviceViewPage");
            return html`<ak-endpoints-device-view
                .deviceId=${args.uuid}
            ></ak-endpoints-device-view>`;
        },
        "device-view",
    ),
    new Route(
        "/endpoints/connectors",
        async () => {
            await import("#admin/endpoints/connectors/ConnectorsListPage");
            return html`<ak-endpoints-connectors-list></ak-endpoints-connectors-list>`;
        },
        "connectors",
    ),
    new Route<{ uuid: string }>(
        "/endpoints/connectors/:uuid",
        async (args) => {
            await import("#admin/endpoints/connectors/ConnectorViewPage");
            return html`<ak-endpoints-connector-view
                .connectorID=${args.uuid}
            ></ak-endpoints-connector-view>`;
        },
        "connector-view",
    ),
    new Route(
        "/endpoints/groups",
        async () => {
            await import("#admin/endpoints/DeviceAccessGroupsListPage");
            return html`<ak-endpoints-device-access-groups-list></ak-endpoints-device-access-groups-list>`;
        },
        "device-access-groups",
    ),

    new Route(
        "/core/sources",
        async () => {
            await import("#admin/sources/SourceListPage");
            return html`<ak-source-list></ak-source-list>`;
        },
        "sources",
    ),
    new Route<{ slug: string }>(
        "/core/sources/:slug",
        async (args) => {
            await import("#admin/sources/SourceViewPage");
            return html`<ak-source-view .sourceSlug=${args.slug}></ak-source-view>`;
        },
        "source-view",
    ),
    new Route(
        "/core/property-mappings",
        async () => {
            await import("#admin/property-mappings/PropertyMappingListPage");
            return html`<ak-property-mapping-list></ak-property-mapping-list>`;
        },
        "property-mappings",
    ),
    new Route(
        "/core/tokens",
        async () => {
            await import("#admin/tokens/TokenListPage");
            return html`<ak-token-list></ak-token-list>`;
        },
        "tokens",
    ),
    new Route(
        "/core/brands",
        async () => {
            await import("#admin/brands/BrandListPage");
            return html`<ak-brand-list></ak-brand-list>`;
        },
        "brands",
    ),

    new Route(
        "/policy/policies",
        async () => {
            await import("#admin/policies/PolicyListPage");
            return html`<ak-policy-list></ak-policy-list>`;
        },
        "policies",
    ),
    new Route(
        "/policy/reputation",
        async () => {
            await import("#admin/policies/reputation/ReputationListPage");
            return html`<ak-policy-reputation-list></ak-policy-reputation-list>`;
        },
        "reputation",
    ),

    new Route(
        "/requests/rules",
        async () => {
            await import("#admin/requests/RequestRuleListPage");
            return html`<ak-request-rule-list></ak-request-rule-list>`;
        },
        "request-rules",
    ),
    new Route(
        "/requests/access-requests",
        async () => {
            await import("#admin/requests/AccessRequestListPage");
            return html`<ak-access-requests-list></ak-access-requests-list>`;
        },
        "access-requests",
    ),

    new Route(
        "/identity/object-attributes",
        async () => {
            await import("#admin/object-attributes/ObjectAttributeListPage");
            return html`<ak-object-attribute-list></ak-object-attribute-list>`;
        },
        "object-attributes",
    ),
    new Route(
        "/identity/groups",
        async () => {
            await import("#admin/groups/GroupListPage");
            return html`<ak-group-list></ak-group-list>`;
        },
        "groups",
    ),
    new Route<{ uuid: string }>(
        "/identity/groups/:uuid",
        async (args) => {
            await import("#admin/groups/GroupViewPage");
            return html`<ak-group-view .groupId=${args.uuid}></ak-group-view>`;
        },
        "group-view",
    ),
    new Route(
        "/identity/agents",
        async () => {
            await import("#admin/agents/AgentListPage");
            return html`<ak-agent-list></ak-agent-list>`;
        },
        "agents",
    ),
    new Route(
        "/identity/users",
        async () => {
            await import("#admin/users/UserListPage");
            return html`<ak-user-list></ak-user-list>`;
        },
        "users",
    ),
    new Route<{ id: string }>(
        // The `{/*}?` tail carries the tab path (`/identity/users/22/credentials`)
        // to this route while `ak-user-view` stays mounted across tab changes.
        "/identity/users/:id{/*}?",
        async (args) => {
            await import("#admin/users/UserViewPage");
            return html`<ak-user-view .userId=${parseInt(args.id, 10)}></ak-user-view>`;
        },
        "user-view",
    ),
    new Route(
        "/identity/roles",
        async () => {
            await import("#admin/roles/ak-role-list");
            return html`<ak-role-list></ak-role-list>`;
        },
        "roles",
    ),
    new Route(
        "/identity/initial-permissions",
        async () => {
            await import("#admin/rbac/ak-initial-permissions-list");
            return html`<ak-initial-permissions-list></ak-initial-permissions-list>`;
        },
        "initial-permissions",
    ),
    new Route<{ id: string }>(
        "/identity/roles/:id",
        async (args) => {
            await import("#admin/roles/ak-role-view");
            return html`<ak-role-view roleId=${args.id}></ak-role-view>`;
        },
        "role-view",
    ),

    new Route(
        "/flow/stages/invitations",
        async () => {
            await import("#admin/stages/invitation/InvitationListPage");
            return html`<ak-stage-invitation-list></ak-stage-invitation-list>`;
        },
        "stage-invitations",
    ),
    new Route(
        "/flow/stages/prompts",
        async () => {
            await import("#admin/stages/prompt/PromptListPage");
            return html`<ak-stage-prompt-list></ak-stage-prompt-list>`;
        },
        "stage-prompts",
    ),
    new Route(
        "/flow/stages",
        async () => {
            await import("#admin/stages/StageListPage");
            return html`<ak-stage-list></ak-stage-list>`;
        },
        "stages",
    ),
    new Route(
        "/flow/flows",
        async () => {
            await import("#admin/flows/FlowListPage");
            return html`<ak-flow-list></ak-flow-list>`;
        },
        "flows",
    ),
    new Route<{ slug: string }>(
        "/flow/flows/:slug",
        async (args) => {
            await import("#admin/flows/FlowViewPage");
            return html`<ak-flow-view
                .flowSlug=${args.slug}
                exportparts="main, tabs"
            ></ak-flow-view>`;
        },
        "flow-view",
    ),

    new Route(
        "/events/log",
        async () => {
            await import("#admin/events/EventListPage");
            return html`<ak-event-list></ak-event-list>`;
        },
        "events",
    ),
    new Route<{ id: string }>(
        "/events/log/:id",
        async (args) => {
            await import("#admin/events/EventViewPage");
            return html`<ak-event-view .eventID=${args.id}></ak-event-view>`;
        },
        "event-view",
    ),
    new Route(
        "/events/transports",
        async () => {
            await import("#admin/events/TransportListPage");
            return html`<ak-event-transport-list></ak-event-transport-list>`;
        },
        "event-transports",
    ),
    new Route(
        "/events/rules",
        async () => {
            await import("#admin/events/RuleListPage");
            return html`<ak-event-rule-list></ak-event-rule-list>`;
        },
        "event-rules",
    ),
    new Route(
        "/events/exports",
        async () => {
            await import("./events/DataExportListPage");
            return html`<ak-data-export-list></ak-data-export-list>`;
        },
        "data-exports",
    ),
    new Route(
        "/events/lifecycle-rules",
        async () => {
            await import("#admin/lifecycle/LifecycleRuleListPage");
            return html`<ak-lifecycle-rule-list></ak-lifecycle-rule-list>`;
        },
        "lifecycle-rules",
    ),
    new Route(
        "/events/lifecycle-reviews",
        async () => {
            await import("#admin/lifecycle/ReviewListPage");
            return html`<ak-review-list></ak-review-list>`;
        },
        "lifecycle-reviews",
    ),
    new Route(
        "/events/offboardings",
        async () => {
            await import("#admin/lifecycle/OffboardingListPage");
            return html`<ak-offboarding-list></ak-offboarding-list>`;
        },
        "offboardings",
    ),

    new Route(
        "/outpost/outposts",
        async () => {
            await import("#admin/outposts/OutpostListPage");
            return html`<ak-outpost-list></ak-outpost-list>`;
        },
        "outposts",
    ),
    new Route<{ id: string }>(
        "/outpost/outposts/:id",
        async (args) => {
            await import("#admin/outposts/OutpostViewPage");
            return html`<ak-outpost-view .outpostID=${args.id}></ak-outpost-view>`;
        },
        "outpost-view",
    ),
    new Route(
        "/outpost/integrations",
        async () => {
            await import("#admin/outposts/ServiceConnectionListPage");
            return html`<ak-outpost-service-connection-list></ak-outpost-service-connection-list>`;
        },
        "integrations",
    ),

    new Route(
        "/crypto/certificates",
        async () => {
            await import("#admin/crypto/CertificateKeyPairListPage");
            return html`<ak-crypto-certificate-list></ak-crypto-certificate-list>`;
        },
        "certificates",
    ),
    new Route(
        "/admin/settings",
        async () => {
            await import("#admin/admin-settings/AdminSettingsPage");
            return html`<ak-admin-settings></ak-admin-settings>`;
        },
        "admin-settings",
    ),
    new Route(
        "/files",
        async () => {
            await import("#admin/files/FileListPage");
            return html`<ak-files-list></ak-files-list>`;
        },
        "files",
    ),
    new Route(
        "/blueprints/instances",
        async () => {
            await import("#admin/blueprints/BlueprintListPage");
            return html`<ak-blueprint-list></ak-blueprint-list>`;
        },
        "blueprints",
    ),
    new Route(
        "/debug",
        async () => {
            await import("#admin/ak-admin-debug-page");
            return html`<ak-admin-debug-page></ak-admin-debug-page>`;
        },
        "debug",
    ),
    new Route(
        "/enterprise/licenses",
        async () => {
            await import("#admin/enterprise/EnterpriseLicenseListPage");
            return html`<ak-enterprise-license-list></ak-enterprise-license-list>`;
        },
        "licenses",
    ),
];
