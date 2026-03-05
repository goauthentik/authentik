import "#admin/admin-overview/AdminOverviewPage";

import { globalAK } from "#common/global";
import { ImportCallback } from "#common/modules/types";

import {
    ID_REGEX as id,
    Route,
    RouteHandler,
    RouteLoader,
    SLUG_REGEX as slug,
    UUID_REGEX as uuid,
} from "#elements/router/Route";

import { html } from "lit";

export type RouteEntry =
    | [pattern: RegExp | string, loader: ImportCallback<object>, handler: RouteHandler]
    | [pattern: RegExp | string, loader: RouteLoader, handler?: RouteHandler];

// prettier-ignore
const routePairs: RouteEntry[] = [
    ["/files", () => import("./files/FileListPage")],
    ["/admin/settings", () => import("./admin-settings/AdminSettingsPage")],

    ["/debug", () => import("./DebugPage")],
    ["/administration/dashboard/users", () => import("./admin-overview/DashboardUserPage")],
    ["/administration/system-tasks", () => import("./admin-overview/SystemTasksPage")],

    ["/core/providers", () => import("./providers/ProviderListPage")],
    [`/core/providers/(?<providerID>${id})`, () => import("./providers/ProviderViewPage")],

    ["/core/applications", () => import("./applications/ApplicationListPage")],
    [`/core/applications/(?<applicationSlug>${slug})`, () => import("./applications/ApplicationViewPage")],

    ["/core/sources", () => import("./sources/SourceListPage")],
    [`/core/sources/(?<sourceSlug>${slug})`, () => import("./sources/SourceViewPage")],

    ["/core/property-mappings", () => import("./property-mappings/PropertyMappingListPage")],

    ["/core/tokens", () => import("./tokens/TokenListPage")],

    ["/core/brands", () => import("./brands/BrandListPage")],

    ["/endpoints/devices", () => import("./endpoints/devices/DeviceListPage")],
    [`/endpoints/devices/(?<deviceID>${uuid})`, () => import("./endpoints/devices/DeviceViewPage")],
    ["/endpoints/connectors", () => import("./endpoints/connectors/ConnectorsListPage")],
    [`/endpoints/connectors/(?<connectorID>${uuid})`, () => import("./endpoints/connectors/ConnectorViewPage")],
    ["/endpoints/groups", () => import("./endpoints/DeviceAccessGroupsListPage")],

    ["/policy/policies", () => import("./policies/PolicyListPage")],
    ["/policy/reputation", () => import("./policies/reputation/ReputationListPage")],

    ["/identity/groups", () => import("./groups/GroupListPage")],
    [`/identity/groups/(?<groupID>${uuid})`, () => import("./groups/GroupViewPage")],

    ["/identity/users", () => import("./users/UserListPage")],
    [`/identity/users/(?<userID>${id})`, () => import("./users/UserViewPage")],

    ["/identity/roles", () => import("./roles/RoleListPage")],
    [`/identity/roles/(?<roleID>${uuid})`, () => import("./roles/RoleViewPage")],

    ["/identity/initial-permissions", () => import("./rbac/InitialPermissionsListPage")],

    ["/flow/flows", () => import("./flows/FlowListPage")],
    [`/flow/flows/(?<flowSlug>${slug})`, () => import("./flows/FlowViewPage")],

    ["/flow/stages", () => import("./stages/StageListPage")],
    ["/flow/stages/invitations", () => import("./stages/invitation/InvitationListPage")],
    ["/flow/stages/prompts", () => import("./stages/prompt/PromptListPage")],

    ["/events/log", () => import("./events/EventListPage")],
    [`/events/log/(?<eventID>${uuid})`, () => import("./events/EventViewPage")],
    ["/events/transports", () => import("./events/TransportListPage")],
    ["/events/rules", () => import("./events/RuleListPage")],
    ["/events/exports", () => import("./events/DataExportListPage")],
    ["/events/lifecycle-rules", () => import("./lifecycle/LifecycleRuleListPage")],
    ["/events/lifecycle-reviews", () => import("./lifecycle/ReviewListPage")],

    ["/outpost/outposts", () => import("./outposts/OutpostListPage")],
    ["/outpost/integrations", () => import("./outposts/ServiceConnectionListPage")],

    ["/crypto/certificates", () => import("./crypto/CertificateKeyPairListPage")],

    ["/blueprints/instances", () => import("./blueprints/BlueprintListPage")],

    ["/enterprise/licenses", () => import("./enterprise/EnterpriseLicenseListPage")],
];

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route({ pattern: new RegExp("^/$") }).redirect("/administration/overview"),
    new Route({ pattern: new RegExp("^#.*") }).redirect("/administration/overview"),
    new Route({ pattern: "/library" }).redirect("/if/user/", true),
    // statically imported since this is the default route
    new Route({
        pattern: "/administration/overview",
        handler: () => html`<ak-admin-overview></ak-admin-overview>`,
    }),
    ...routePairs.map(([pattern, loader, handler]) => new Route({ pattern, loader, handler })),
];

/**
 * Application route helpers.
 *
 * @TODO: This API isn't quite right yet. Revisit after the hash router is replaced.
 */
export const ApplicationRoute = {
    EditURL(slug: string, base = globalAK().api.base) {
        return `${base}if/admin/#/core/applications/${slug}`;
    },
} as const;
