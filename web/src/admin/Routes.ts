import "@goauthentik/admin/admin-overview/AdminOverviewPage";
import { Route } from "@goauthentik/elements/router/Route";
import { ID_PATTERN, SLUG_PATTERN, UUID_PATTERN } from "@goauthentik/elements/router/constants";

import { html } from "lit";

interface IDParameters {
    id: string;
}

interface SlugParameters {
    slug: string;
}

interface UUIDParameters {
    uuid: string;
}

export const ROUTES = [
    // Prevent infinite Shell loops
    Route.redirect("^/$", "/administration/overview"),
    Route.redirect("^#.*", "/administration/overview"),
    Route.redirect("^/library$", "/if/user/", true),
    // statically imported since this is the default route
    new Route("/administration/overview", () => {
        return html`<ak-admin-overview></ak-admin-overview>`;
    }),
    new Route("/administration/dashboard/users", async () => {
        await import("@goauthentik/admin/admin-overview/DashboardUserPage");

        return html`<ak-admin-dashboard-users></ak-admin-dashboard-users>`;
    }),
    new Route("/administration/system-tasks", async () => {
        await import("@goauthentik/admin/system-tasks/SystemTaskListPage");

        return html`<ak-system-task-list></ak-system-task-list>`;
    }),
    new Route("/core/providers", async () => {
        await import("@goauthentik/admin/providers/ProviderListPage");

        return html`<ak-provider-list></ak-provider-list>`;
    }),
    new Route<IDParameters>(
        new URLPattern({
            pathname: `/core/providers/:id(${ID_PATTERN})`,
        }),
        async (params) => {
            await import("@goauthentik/admin/providers/ProviderViewPage");

            return html`<ak-provider-view
                .providerID=${parseInt(params.id, 10)}
            ></ak-provider-view>`;
        },
    ),
    new Route("/core/applications", async () => {
        await import("@goauthentik/admin/applications/ApplicationListPage");

        return html`<ak-application-list></ak-application-list>`;
    }),
    new Route(`/core/applications/:slug(${SLUG_PATTERN})`, async ({ slug }) => {
        await import("@goauthentik/admin/applications/ApplicationViewPage");

        return html`<ak-application-view .applicationSlug=${slug}></ak-application-view>`;
    }),
    new Route("/core/sources", async () => {
        await import("@goauthentik/admin/sources/SourceListPage");

        return html`<ak-source-list></ak-source-list>`;
    }),
    new Route(`/core/sources/:slug(${SLUG_PATTERN})`, async ({ slug }) => {
        await import("@goauthentik/admin/sources/SourceViewPage");

        return html`<ak-source-view .sourceSlug=${slug}></ak-source-view>`;
    }),
    new Route("/core/property-mappings", async () => {
        await import("@goauthentik/admin/property-mappings/PropertyMappingListPage");

        return html`<ak-property-mapping-list></ak-property-mapping-list>`;
    }),
    new Route("/core/tokens", async () => {
        await import("@goauthentik/admin/tokens/TokenListPage");

        return html`<ak-token-list></ak-token-list>`;
    }),
    new Route("/core/brands", async () => {
        await import("@goauthentik/admin/brands/BrandListPage");

        return html`<ak-brand-list></ak-brand-list>`;
    }),
    new Route("/policy/policies", async () => {
        await import("@goauthentik/admin/policies/PolicyListPage");

        return html`<ak-policy-list></ak-policy-list>`;
    }),
    new Route("/policy/reputation", async () => {
        await import("@goauthentik/admin/policies/reputation/ReputationListPage");

        return html`<ak-policy-reputation-list></ak-policy-reputation-list>`;
    }),
    new Route("/identity/groups", async () => {
        await import("@goauthentik/admin/groups/GroupListPage");

        return html`<ak-group-list></ak-group-list>`;
    }),
    new Route<UUIDParameters>(`/identity/groups/:uuid(${UUID_PATTERN})`, async ({ uuid }) => {
        await import("@goauthentik/admin/groups/GroupViewPage");

        return html`<ak-group-view .groupId=${uuid}></ak-group-view>`;
    }),
    new Route("/identity/users", async () => {
        await import("@goauthentik/admin/users/UserListPage");

        return html`<ak-user-list></ak-user-list>`;
    }),
    new Route<IDParameters>(`/identity/users/:id(${ID_PATTERN})`, async ({ id }) => {
        await import("@goauthentik/admin/users/UserViewPage");

        return html`<ak-user-view .userId=${parseInt(id, 10)}></ak-user-view>`;
    }),
    new Route("/identity/roles", async () => {
        await import("@goauthentik/admin/roles/RoleListPage");

        return html`<ak-role-list></ak-role-list>`;
    }),
    new Route<IDParameters>(`/identity/roles/:id(${UUID_PATTERN})`, async ({ id }) => {
        await import("@goauthentik/admin/roles/RoleViewPage");

        return html`<ak-role-view roleId=${id}></ak-role-view>`;
    }),
    new Route("/flow/stages/invitations", async () => {
        await import("@goauthentik/admin/stages/invitation/InvitationListPage");

        return html`<ak-stage-invitation-list></ak-stage-invitation-list>`;
    }),
    new Route("/flow/stages/prompts", async () => {
        await import("@goauthentik/admin/stages/prompt/PromptListPage");

        return html`<ak-stage-prompt-list></ak-stage-prompt-list>`;
    }),
    new Route("/flow/stages", async () => {
        await import("@goauthentik/admin/stages/StageListPage");

        return html`<ak-stage-list></ak-stage-list>`;
    }),
    new Route("/flow/flows", async () => {
        await import("@goauthentik/admin/flows/FlowListPage");

        return html`<ak-flow-list></ak-flow-list>`;
    }),
    new Route<SlugParameters>(`/flow/flows/:slug(${SLUG_PATTERN})`, async ({ slug }) => {
        await import("@goauthentik/admin/flows/FlowViewPage");

        return html`<ak-flow-view .flowSlug=${slug}></ak-flow-view>`;
    }),
    new Route("/events/log", async () => {
        await import("@goauthentik/admin/events/EventListPage");

        return html`<ak-event-list></ak-event-list>`;
    }),
    new Route<IDParameters>(`/events/log/:id(${UUID_PATTERN})`, async ({ id }) => {
        await import("@goauthentik/admin/events/EventViewPage");

        return html`<ak-event-view .eventID=${id}></ak-event-view>`;
    }),
    new Route("/events/transports", async () => {
        await import("@goauthentik/admin/events/TransportListPage");

        return html`<ak-event-transport-list></ak-event-transport-list>`;
    }),
    new Route("/events/rules", async () => {
        await import("@goauthentik/admin/events/RuleListPage");

        return html`<ak-event-rule-list></ak-event-rule-list>`;
    }),
    new Route("/outpost/outposts", async () => {
        await import("@goauthentik/admin/outposts/OutpostListPage");

        return html`<ak-outpost-list></ak-outpost-list>`;
    }),
    new Route("/outpost/integrations", async () => {
        await import("@goauthentik/admin/outposts/ServiceConnectionListPage");

        return html`<ak-outpost-service-connection-list></ak-outpost-service-connection-list>`;
    }),
    new Route("/crypto/certificates", async () => {
        await import("@goauthentik/admin/crypto/CertificateKeyPairListPage");

        return html`<ak-crypto-certificate-list></ak-crypto-certificate-list>`;
    }),
    new Route("/admin/settings", async () => {
        await import("@goauthentik/admin/admin-settings/AdminSettingsPage");

        return html`<ak-admin-settings></ak-admin-settings>`;
    }),
    new Route("/blueprints/instances", async () => {
        await import("@goauthentik/admin/blueprints/BlueprintListPage");

        return html`<ak-blueprint-list></ak-blueprint-list>`;
    }),
    new Route("/debug", async () => {
        await import("@goauthentik/admin/DebugPage");

        return html`<ak-admin-debug-page></ak-admin-debug-page>`;
    }),
    new Route("/enterprise/licenses", async () => {
        await import("@goauthentik/admin/enterprise/EnterpriseLicenseListPage");

        return html`<ak-enterprise-license-list></ak-enterprise-license-list>`;
    }),
] satisfies Route<never>[];
