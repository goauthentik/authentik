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
        "/administration/system-tasks{/*}?",
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
    new Route(
        "/core/providers/new",
        async () => {
            await import("#admin/providers/ak-provider-wizard");

            return html`<ak-provider-wizard-page></ak-provider-wizard-page>`;
        },
        "provider-new",
    ),
    new Route<{ id: string }>(
        "/core/providers/:id{/*}?",
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
        "/core/applications/:slug{/*}?",
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
        "/endpoints/devices/:uuid{/*}?",
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
    new Route(
        "/endpoints/connectors/new",
        async () => {
            await import("#admin/endpoints/connectors/ConnectorWizard");

            return html`<ak-endpoint-connector-wizard-page></ak-endpoint-connector-wizard-page>`;
        },
        "connector-new",
    ),
    new Route<{ uuid: string }>(
        "/endpoints/connectors/:uuid{/*}?",
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
        "/endpoints/groups/new",
        async () => {
            await import("#admin/endpoints/DeviceAccessGroupForm");

            return html`<ak-endpoints-device-access-groups-form-page></ak-endpoints-device-access-groups-form-page>`;
        },
        "device-access-group-new",
    ),

    new Route(
        "/core/sources",
        async () => {
            await import("#admin/sources/SourceListPage");

            return html`<ak-source-list></ak-source-list>`;
        },
        "sources",
    ),
    new Route(
        "/core/sources/new",
        async () => {
            await import("#admin/sources/ak-source-wizard");

            return html`<ak-source-wizard-page></ak-source-wizard-page>`;
        },
        "source-new",
    ),
    new Route<{ slug: string }>(
        "/core/sources/:slug{/*}?",
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
        "/core/property-mappings/new",
        async () => {
            await import("#admin/property-mappings/ak-property-mapping-wizard");

            return html`<ak-property-mapping-wizard-page></ak-property-mapping-wizard-page>`;
        },
        "property-mapping-new",
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
        "/core/tokens/new",
        async () => {
            await import("#admin/tokens/TokenForm");

            return html`<ak-token-form-page></ak-token-form-page>`;
        },
        "token-new",
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
        "/core/brands/new",
        async () => {
            await import("#admin/brands/BrandForm");

            return html`<ak-brand-form-page></ak-brand-form-page>`;
        },
        "brand-new",
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
        "/policy/policies/new",
        async () => {
            await import("#admin/policies/ak-policy-wizard");

            return html`<ak-policy-wizard-page></ak-policy-wizard-page>`;
        },
        "policy-new",
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
        "/requests/rules/new",
        async () => {
            await import("#admin/requests/RequestRuleForm");

            return html`<ak-request-rule-form-page></ak-request-rule-form-page>`;
        },
        "request-rule-new",
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
        "/identity/object-attributes/new",
        async () => {
            await import("#admin/object-attributes/ObjectAttributeForm");

            return html`<ak-object-attribute-form-page></ak-object-attribute-form-page>`;
        },
        "object-attribute-new",
    ),
    new Route(
        "/identity/groups",
        async () => {
            await import("#admin/groups/GroupListPage");

            return html`<ak-group-list></ak-group-list>`;
        },
        "groups",
    ),
    new Route(
        "/identity/groups/new",
        async () => {
            await import("#admin/groups/ak-group-form");

            return html`<ak-group-form-page></ak-group-form-page>`;
        },
        "group-new",
    ),
    new Route<{ uuid: string }>(
        "/identity/groups/:uuid{/*}?",
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
        "/identity/agents/new",
        async () => {
            await import("#admin/agents/AgentForm");

            return html`<ak-agent-form-page></ak-agent-form-page>`;
        },
        "agent-new",
    ),
    new Route(
        "/identity/users",
        async () => {
            await import("#admin/users/UserListPage");

            return html`<ak-user-list></ak-user-list>`;
        },
        "users",
    ),
    new Route(
        "/identity/users/new",
        async () => {
            await import("#admin/users/ak-user-wizard");

            return html`<ak-user-wizard-page></ak-user-wizard-page>`;
        },
        "user-new",
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
        "/identity/roles/new",
        async () => {
            await import("#admin/roles/ak-role-form");

            return html`<ak-role-form-page></ak-role-form-page>`;
        },
        "role-new",
    ),
    new Route(
        "/identity/initial-permissions",
        async () => {
            await import("#admin/rbac/ak-initial-permissions-list");

            return html`<ak-initial-permissions-list></ak-initial-permissions-list>`;
        },
        "initial-permissions",
    ),
    new Route(
        "/identity/initial-permissions/new",
        async () => {
            await import("#admin/rbac/ak-initial-permissions-form");

            return html`<ak-initial-permissions-form-page></ak-initial-permissions-form-page>`;
        },
        "initial-permissions-new",
    ),
    new Route<{ id: string }>(
        "/identity/roles/:id{/*}?",
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
        "/flow/stages/prompts/new",
        async () => {
            await import("#admin/stages/prompt/PromptForm");

            return html`<ak-prompt-form-page></ak-prompt-form-page>`;
        },
        "prompt-new",
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
        "/flow/stages/new",
        async () => {
            await import("#admin/stages/ak-stage-wizard");

            return html`<ak-stage-wizard-page></ak-stage-wizard-page>`;
        },
        "stage-new",
    ),
    new Route(
        "/flow/flows",
        async () => {
            await import("#admin/flows/FlowListPage");

            return html`<ak-flow-list></ak-flow-list>`;
        },
        "flows",
    ),
    new Route(
        "/flow/flows/new",
        async () => {
            await import("#admin/flows/FlowForm");

            return html`<ak-flow-form-page></ak-flow-form-page>`;
        },
        "flow-new",
    ),
    new Route<{ slug: string }>(
        "/flow/flows/:slug{/*}?",
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
        "/events/transports/new",
        async () => {
            await import("#admin/events/TransportForm");

            return html`<ak-event-transport-form-page></ak-event-transport-form-page>`;
        },
        "notification-transport-new",
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
        "/events/rules/new",
        async () => {
            await import("#admin/events/RuleForm");

            return html`<ak-event-rule-form-page></ak-event-rule-form-page>`;
        },
        "notification-rule-new",
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
        "/events/lifecycle-rules/new",
        async () => {
            await import("#admin/lifecycle/LifecycleRuleForm");

            return html`<ak-lifecycle-rule-form-page></ak-lifecycle-rule-form-page>`;
        },
        "lifecycle-rule-new",
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
    new Route(
        "/outpost/outposts/new",
        async () => {
            await import("#admin/outposts/OutpostForm");

            return html`<ak-outpost-form-page></ak-outpost-form-page>`;
        },
        "outpost-new",
    ),
    new Route<{ id: string }>(
        "/outpost/outposts/:id{/*}?",
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
        "/outpost/integrations/new",
        async () => {
            await import("#admin/outposts/ak-service-connection-wizard");

            return html`<ak-service-connection-wizard-page></ak-service-connection-wizard-page>`;
        },
        "integration-new",
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
        "/crypto/certificates/new",
        async () => {
            await import("#admin/crypto/CertificateKeyPairForm");

            return html`<ak-crypto-certificate-form-page></ak-crypto-certificate-form-page>`;
        },
        "certificate-new",
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
        "/files/new",
        async () => {
            await import("#admin/files/FileUploadForm");

            return html`<ak-file-upload-form-page></ak-file-upload-form-page>`;
        },
        "file-new",
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
        "/blueprints/instances/new",
        async () => {
            await import("#admin/blueprints/BlueprintForm");

            return html`<ak-blueprint-form-page></ak-blueprint-form-page>`;
        },
        "blueprint-new",
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
    new Route(
        "/enterprise/licenses/new",
        async () => {
            await import("#admin/enterprise/EnterpriseLicenseForm");

            return html`<ak-enterprise-license-form-page></ak-enterprise-license-form-page>`;
        },
        "license-new",
    ),
];
