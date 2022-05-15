import { html } from "lit";

import { ID_REGEX, Route, SLUG_REGEX, UUID_REGEX } from "./elements/router/Route";
import "./pages/admin-overview/AdminOverviewPage";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/administration/overview"),
    new Route(new RegExp("^#.*")).redirect("/administration/overview"),
    new Route(new RegExp("^/library$")).redirect("/if/user/", true),
    // statically imported since this is the default route
    new Route(new RegExp("^/administration/overview$"), async () => {
        return html`<ak-admin-overview></ak-admin-overview>`;
    }),
    new Route(new RegExp("^/administration/dashboard/users$"), async () => {
        await import("./pages/admin-overview/DashboardUserPage");
        return html`<ak-admin-dashboard-users></ak-admin-dashboard-users>`;
    }),
    new Route(new RegExp("^/administration/system-tasks$"), async () => {
        await import("./pages/system-tasks/SystemTaskListPage");
        return html`<ak-system-task-list></ak-system-task-list>`;
    }),
    new Route(new RegExp("^/core/providers$"), async () => {
        await import("./pages/providers/ProviderListPage");
        return html`<ak-provider-list></ak-provider-list>`;
    }),
    new Route(new RegExp(`^/core/providers/(?<id>${ID_REGEX})$`), async (args) => {
        await import("./pages/providers/ProviderViewPage");
        return html`<ak-provider-view .providerID=${parseInt(args.id, 10)}></ak-provider-view>`;
    }),
    new Route(new RegExp("^/core/applications$"), async () => {
        await import("./pages/applications/ApplicationListPage");
        return html`<ak-application-list></ak-application-list>`;
    }),
    new Route(new RegExp(`^/core/applications/(?<slug>${SLUG_REGEX})$`), async (args) => {
        await import("./pages/applications/ApplicationViewPage");
        return html`<ak-application-view .applicationSlug=${args.slug}></ak-application-view>`;
    }),
    new Route(new RegExp("^/core/sources$"), async () => {
        await import("./pages/sources/SourceListPage");
        return html`<ak-source-list></ak-source-list>`;
    }),
    new Route(new RegExp(`^/core/sources/(?<slug>${SLUG_REGEX})$`), async (args) => {
        await import("./pages/sources/SourceViewPage");
        return html`<ak-source-view .sourceSlug=${args.slug}></ak-source-view>`;
    }),
    new Route(new RegExp("^/core/property-mappings$"), async () => {
        await import("./pages/property-mappings/PropertyMappingListPage");
        return html`<ak-property-mapping-list></ak-property-mapping-list>`;
    }),
    new Route(new RegExp("^/core/tokens$"), async () => {
        await import("./pages/tokens/TokenListPage");
        return html`<ak-token-list></ak-token-list>`;
    }),
    new Route(new RegExp("^/core/tenants$"), async () => {
        await import("./pages/tenants/TenantListPage");
        return html`<ak-tenant-list></ak-tenant-list>`;
    }),
    new Route(new RegExp("^/policy/policies$"), async () => {
        await import("./pages/policies/PolicyListPage");
        return html`<ak-policy-list></ak-policy-list>`;
    }),
    new Route(new RegExp("^/policy/reputation$"), async () => {
        await import("./pages/policies/reputation/ReputationListPage");
        return html`<ak-policy-reputation-list></ak-policy-reputation-list>`;
    }),
    new Route(new RegExp("^/identity/groups$"), async () => {
        await import("./pages/groups/GroupListPage");
        return html`<ak-group-list></ak-group-list>`;
    }),
    new Route(new RegExp(`^/identity/groups/(?<uuid>${UUID_REGEX})$`), async (args) => {
        await import("./pages/groups/GroupViewPage");
        return html`<ak-group-view .groupId=${args.uuid}></ak-group-view>`;
    }),
    new Route(new RegExp("^/identity/users$"), async () => {
        await import("./pages/users/UserListPage");
        return html`<ak-user-list></ak-user-list>`;
    }),
    new Route(new RegExp(`^/identity/users/(?<id>${ID_REGEX})$`), async (args) => {
        await import("./pages/users/UserViewPage");
        return html`<ak-user-view .userId=${parseInt(args.id, 10)}></ak-user-view>`;
    }),
    new Route(new RegExp("^/flow/stages/invitations$"), async () => {
        await import("./pages/stages/invitation/InvitationListPage");
        return html`<ak-stage-invitation-list></ak-stage-invitation-list>`;
    }),
    new Route(new RegExp("^/flow/stages/prompts$"), async () => {
        await import("./pages/stages/prompt/PromptListPage");
        return html`<ak-stage-prompt-list></ak-stage-prompt-list>`;
    }),
    new Route(new RegExp("^/flow/stages$"), async () => {
        await import("./pages/stages/StageListPage");
        return html`<ak-stage-list></ak-stage-list>`;
    }),
    new Route(new RegExp("^/flow/flows$"), async () => {
        await import("./pages/flows/FlowListPage");
        return html`<ak-flow-list></ak-flow-list>`;
    }),
    new Route(new RegExp(`^/flow/flows/(?<slug>${SLUG_REGEX})$`), async (args) => {
        await import("./pages/flows/FlowViewPage");
        return html`<ak-flow-view .flowSlug=${args.slug}></ak-flow-view>`;
    }),
    new Route(new RegExp("^/events/log$"), async () => {
        await import("./pages/events/EventListPage");
        return html`<ak-event-list></ak-event-list>`;
    }),
    new Route(new RegExp(`^/events/log/(?<id>${UUID_REGEX})$`), async (args) => {
        await import("./pages/events/EventInfoPage");
        return html`<ak-event-info-page .eventID=${args.id}></ak-event-info-page>`;
    }),
    new Route(new RegExp("^/events/transports$"), async () => {
        await import("./pages/events/TransportListPage");
        return html`<ak-event-transport-list></ak-event-transport-list>`;
    }),
    new Route(new RegExp("^/events/rules$"), async () => {
        await import("./pages/events/RuleListPage");
        return html`<ak-event-rule-list></ak-event-rule-list>`;
    }),
    new Route(new RegExp("^/outpost/outposts$"), async () => {
        await import("./pages/outposts/OutpostListPage");
        return html`<ak-outpost-list></ak-outpost-list>`;
    }),
    new Route(new RegExp("^/outpost/integrations$"), async () => {
        await import("./pages/outposts/ServiceConnectionListPage");
        return html`<ak-outpost-service-connection-list></ak-outpost-service-connection-list>`;
    }),
    new Route(new RegExp("^/crypto/certificates$"), async () => {
        await import("./pages/crypto/CertificateKeyPairListPage");
        return html`<ak-crypto-certificate-list></ak-crypto-certificate-list>`;
    }),
];
