import { html } from "lit";

import { ID_REGEX, Route, SLUG_REGEX, UUID_REGEX } from "./elements/router/Route";
import "./pages/admin-overview/AdminOverviewPage";
import "./pages/applications/ApplicationListPage";
import "./pages/applications/ApplicationViewPage";
import "./pages/crypto/CertificateKeyPairListPage";
import "./pages/events/EventInfoPage";
import "./pages/events/EventListPage";
import "./pages/events/RuleListPage";
import "./pages/events/TransportListPage";
import "./pages/flows/FlowListPage";
import "./pages/flows/FlowViewPage";
import "./pages/groups/GroupListPage";
import "./pages/outposts/OutpostListPage";
import "./pages/outposts/ServiceConnectionListPage";
import "./pages/policies/PolicyListPage";
import "./pages/policies/reputation/IPReputationListPage";
import "./pages/policies/reputation/UserReputationListPage";
import "./pages/property-mappings/PropertyMappingListPage";
import "./pages/providers/ProviderListPage";
import "./pages/providers/ProviderViewPage";
import "./pages/sources/SourceViewPage";
import "./pages/sources/SourcesListPage";
import "./pages/stages/StageListPage";
import "./pages/stages/invitation/InvitationListPage";
import "./pages/stages/prompt/PromptListPage";
import "./pages/system-tasks/SystemTaskListPage";
import "./pages/tenants/TenantListPage";
import "./pages/tokens/TokenListPage";
import "./pages/users/UserListPage";
import "./pages/users/UserViewPage";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/administration/overview"),
    new Route(new RegExp("^#.*")).redirect("/administration/overview"),
    new Route(new RegExp("^/library$")).redirectRaw("/if/user/"),
    new Route(
        new RegExp("^/administration/overview$"),
        html`<ak-admin-overview></ak-admin-overview>`,
    ),
    new Route(
        new RegExp("^/administration/system-tasks$"),
        html`<ak-system-task-list></ak-system-task-list>`,
    ),
    new Route(new RegExp("^/core/providers$"), html`<ak-provider-list></ak-provider-list>`),
    new Route(new RegExp(`^/core/providers/(?<id>${ID_REGEX})$`)).then((args) => {
        return html`<ak-provider-view .providerID=${parseInt(args.id, 10)}></ak-provider-view>`;
    }),
    new Route(
        new RegExp("^/core/applications$"),
        html`<ak-application-list></ak-application-list>`,
    ),
    new Route(new RegExp(`^/core/applications/(?<slug>${SLUG_REGEX})$`)).then((args) => {
        return html`<ak-application-view .applicationSlug=${args.slug}></ak-application-view>`;
    }),
    new Route(new RegExp("^/core/sources$"), html`<ak-source-list></ak-source-list>`),
    new Route(new RegExp(`^/core/sources/(?<slug>${SLUG_REGEX})$`)).then((args) => {
        return html`<ak-source-view .sourceSlug=${args.slug}></ak-source-view>`;
    }),
    new Route(
        new RegExp("^/core/property-mappings$"),
        html`<ak-property-mapping-list></ak-property-mapping-list>`,
    ),
    new Route(new RegExp("^/core/tokens$"), html`<ak-token-list></ak-token-list>`),
    new Route(new RegExp("^/core/tenants$"), html`<ak-tenant-list></ak-tenant-list>`),
    new Route(new RegExp("^/policy/policies$"), html`<ak-policy-list></ak-policy-list>`),
    new Route(
        new RegExp("^/policy/reputation/ip$"),
        html`<ak-policy-reputation-ip-list></ak-policy-reputation-ip-list>`,
    ),
    new Route(
        new RegExp("^/policy/reputation/user$"),
        html`<ak-policy-reputation-user-list></ak-policy-reputation-user-list>`,
    ),
    new Route(new RegExp("^/identity/groups$"), html`<ak-group-list></ak-group-list>`),
    new Route(new RegExp("^/identity/users$"), html`<ak-user-list></ak-user-list>`),
    new Route(new RegExp(`^/identity/users/(?<id>${ID_REGEX})$`)).then((args) => {
        return html`<ak-user-view .userId=${parseInt(args.id, 10)}></ak-user-view>`;
    }),
    new Route(
        new RegExp("^/flow/stages/invitations$"),
        html`<ak-stage-invitation-list></ak-stage-invitation-list>`,
    ),
    new Route(
        new RegExp("^/flow/stages/prompts$"),
        html`<ak-stage-prompt-list></ak-stage-prompt-list>`,
    ),
    new Route(new RegExp("^/flow/stages$"), html`<ak-stage-list></ak-stage-list>`),
    new Route(new RegExp("^/flow/flows$"), html`<ak-flow-list></ak-flow-list>`),
    new Route(new RegExp(`^/flow/flows/(?<slug>${SLUG_REGEX})$`)).then((args) => {
        return html`<ak-flow-view .flowSlug=${args.slug}></ak-flow-view>`;
    }),
    new Route(new RegExp("^/events/log$"), html`<ak-event-list></ak-event-list>`),
    new Route(new RegExp(`^/events/log/(?<id>${UUID_REGEX})$`)).then((args) => {
        return html`<ak-event-info-page .eventID=${args.id}></ak-event-info-page>`;
    }),
    new Route(
        new RegExp("^/events/transports$"),
        html`<ak-event-transport-list></ak-event-transport-list>`,
    ),
    new Route(new RegExp("^/events/rules$"), html`<ak-event-rule-list></ak-event-rule-list>`),
    new Route(new RegExp("^/outpost/outposts$"), html`<ak-outpost-list></ak-outpost-list>`),
    new Route(
        new RegExp("^/outpost/integrations$"),
        html`<ak-outpost-service-connection-list></ak-outpost-service-connection-list>`,
    ),
    new Route(
        new RegExp("^/crypto/certificates$"),
        html`<ak-crypto-certificate-list></ak-crypto-certificate-list>`,
    ),
];
