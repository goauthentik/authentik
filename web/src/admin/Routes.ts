import "@goauthentik/admin/admin-overview/AdminOverviewPage";
import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "@goauthentik/elements/router/Route";
import { RawRoute, makeRoute } from "@goauthentik/elements/router/routeUtils";

import { html } from "lit";

export const _ROUTES: RawRoute[] = [
    // Prevent infinite Shell loops
    ["^/$", "/administration/overview"],
    ["^#.*", "/administration/overview"],
    ["^/library$", ["/if/user/", true]],
    // statically imported since this is the default route
    [
        "^/administration/overview$",
        async () => {
            return html`<ak-admin-overview></ak-admin-overview>`;
        },
    ],
    [
        "^/administration/dashboard/users$",
        async () => {
            await import("@goauthentik/admin/admin-overview/DashboardUserPage");
            return html`<ak-admin-dashboard-users></ak-admin-dashboard-users>`;
        },
    ],
    [
        "^/administration/system-tasks$",
        async () => {
            await import("@goauthentik/admin/system-tasks/SystemTaskListPage");
            return html`<ak-system-task-list></ak-system-task-list>`;
        },
    ],
    [
        "^/core/providers$",
        async () => {
            await import("@goauthentik/admin/providers/ProviderListPage");
            return html`<ak-provider-list></ak-provider-list>`;
        },
    ],
    [
        `^/core/providers/(?<id>${ID_REGEX}])$`,
        async (args) => {
            await import("@goauthentik/admin/providers/ProviderViewPage");
            return html`<ak-provider-view .providerID=${parseInt(args.id, 10)}></ak-provider-view>`;
        },
    ],
    [
        "^/core/applications$",
        async () => {
            await import("@goauthentik/admin/applications/ApplicationListPage");
            return html`<ak-application-list></ak-application-list>`;
        },
    ],
    [
        `^/core/applications/(?<slug>${SLUG_REGEX})$`,
        async (args) => {
            await import("@goauthentik/admin/applications/ApplicationViewPage");
            return html`<ak-application-view .applicationSlug=${args.slug}></ak-application-view>`;
        },
    ],
    [
        "^/core/sources$",
        async () => {
            await import("@goauthentik/admin/sources/SourceListPage");
            return html`<ak-source-list></ak-source-list>`;
        },
    ],
    [
        `^/core/sources/(?<slug>${SLUG_REGEX})$`,
        async (args) => {
            await import("@goauthentik/admin/sources/SourceViewPage");
            return html`<ak-source-view .sourceSlug=${args.slug}></ak-source-view>`;
        },
    ],
    [
        "^/core/property-mappings$",
        async () => {
            await import("@goauthentik/admin/property-mappings/PropertyMappingListPage");
            return html`<ak-property-mapping-list></ak-property-mapping-list>`;
        },
    ],
    [
        "^/core/tokens$",
        async () => {
            await import("@goauthentik/admin/tokens/TokenListPage");
            return html`<ak-token-list></ak-token-list>`;
        },
    ],
    [
        "^/core/brands",
        async () => {
            await import("@goauthentik/admin/brands/BrandListPage");
            return html`<ak-brand-list></ak-brand-list>`;
        },
    ],
    [
        "^/policy/policies$",
        async () => {
            await import("@goauthentik/admin/policies/PolicyListPage");
            return html`<ak-policy-list></ak-policy-list>`;
        },
    ],
    [
        "^/policy/reputation$",
        async () => {
            await import("@goauthentik/admin/policies/reputation/ReputationListPage");
            return html`<ak-policy-reputation-list></ak-policy-reputation-list>`;
        },
    ],
    [
        "^/identity/groups$",
        async () => {
            await import("@goauthentik/admin/groups/GroupListPage");
            return html`<ak-group-list></ak-group-list>`;
        },
    ],
    [
        `^/identity/groups/(?<uuid>${UUID_REGEX})$`,
        async (args) => {
            await import("@goauthentik/admin/groups/GroupViewPage");
            return html`<ak-group-view .groupId=${args.uuid}></ak-group-view>`;
        },
    ],
    [
        "^/identity/users$",
        async () => {
            await import("@goauthentik/admin/users/UserListPage");
            return html`<ak-user-list></ak-user-list>`;
        },
    ],
    [
        `^/identity/users/(?<id>${ID_REGEX})$`,
        async (args) => {
            await import("@goauthentik/admin/users/UserViewPage");
            return html`<ak-user-view .userId=${parseInt(args.id, 10)}></ak-user-view>`;
        },
    ],
    [
        "^/identity/roles$",
        async () => {
            await import("@goauthentik/admin/roles/RoleListPage");
            return html`<ak-role-list></ak-role-list>`;
        },
    ],
    [
        `^/identity/roles/(?<id>${UUID_REGEX})$`,
        async (args) => {
            await import("@goauthentik/admin/roles/RoleViewPage");
            return html`<ak-role-view roleId=${args.id}></ak-role-view>`;
        },
    ],
    [
        "^/flow/stages/invitations$",
        async () => {
            await import("@goauthentik/admin/stages/invitation/InvitationListPage");
            return html`<ak-stage-invitation-list></ak-stage-invitation-list>`;
        },
    ],
    [
        "^/flow/stages/prompts$",
        async () => {
            await import("@goauthentik/admin/stages/prompt/PromptListPage");
            return html`<ak-stage-prompt-list></ak-stage-prompt-list>`;
        },
    ],
    [
        "^/flow/stages$",
        async () => {
            await import("@goauthentik/admin/stages/StageListPage");
            return html`<ak-stage-list></ak-stage-list>`;
        },
    ],
    [
        "^/flow/flows$",
        async () => {
            await import("@goauthentik/admin/flows/FlowListPage");
            return html`<ak-flow-list></ak-flow-list>`;
        },
    ],
    [
        `^/flow/flows/(?<slug>${SLUG_REGEX})$`,
        async (args) => {
            await import("@goauthentik/admin/flows/FlowViewPage");
            return html`<ak-flow-view .flowSlug=${args.slug}></ak-flow-view>`;
        },
    ],
    [
        "^/events/log$",
        async () => {
            await import("@goauthentik/admin/events/EventListPage");
            return html`<ak-event-list></ak-event-list>`;
        },
    ],
    [
        `^/events/log/(?<id>${UUID_REGEX})$`,
        async (args) => {
            await import("@goauthentik/admin/events/EventViewPage");
            return html`<ak-event-view .eventID=${args.id}></ak-event-view>`;
        },
    ],
    [
        "^/events/transports$",
        async () => {
            await import("@goauthentik/admin/events/TransportListPage");
            return html`<ak-event-transport-list></ak-event-transport-list>`;
        },
    ],
    [
        "^/events/rules$",
        async () => {
            await import("@goauthentik/admin/events/RuleListPage");
            return html`<ak-event-rule-list></ak-event-rule-list>`;
        },
    ],
    [
        "^/outpost/outposts$",
        async () => {
            await import("@goauthentik/admin/outposts/OutpostListPage");
            return html`<ak-outpost-list></ak-outpost-list>`;
        },
    ],
    [
        "^/outpost/integrations$",
        async () => {
            await import("@goauthentik/admin/outposts/ServiceConnectionListPage");
            return html`<ak-outpost-service-connection-list></ak-outpost-service-connection-list>`;
        },
    ],
    [
        "^/crypto/certificates$",
        async () => {
            await import("@goauthentik/admin/crypto/CertificateKeyPairListPage");
            return html`<ak-crypto-certificate-list></ak-crypto-certificate-list>`;
        },
    ],
    [
        "^/admin/settings$",
        async () => {
            await import("@goauthentik/admin/admin-settings/AdminSettingsPage");
            return html`<ak-admin-settings></ak-admin-settings>`;
        },
    ],
    [
        "^/blueprints/instances$",
        async () => {
            await import("@goauthentik/admin/blueprints/BlueprintListPage");
            return html`<ak-blueprint-list></ak-blueprint-list>`;
        },
    ],
    [
        "^/debug$",
        async () => {
            await import("@goauthentik/admin/DebugPage");
            return html`<ak-admin-debug-page></ak-admin-debug-page>`;
        },
    ],
    [
        "^/enterprise/licenses$",
        async () => {
            await import("@goauthentik/admin/enterprise/EnterpriseLicenseListPage");
            return html`<ak-enterprise-license-list></ak-enterprise-license-list>`;
        },
    ],
];

export const ROUTES = _ROUTES.map(makeRoute);
