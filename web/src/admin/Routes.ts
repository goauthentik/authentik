import "#admin/admin-overview/AdminOverviewPage";

import { globalAK } from "#common/global";

import {
    ID_REGEX as id,
    Route,
    SLUG_REGEX as slug,
    UUID_REGEX as uuid,
} from "#elements/router/Route";
import { collateRoutes, RouteEntry } from "#elements/router/shared";

import { html } from "lit";

// prettier-ignore
const routePairs: RouteEntry[] = collateRoutes([
    ["admin/settings", () => import("./admin-settings/AdminSettingsPage")],

    ["administration", [
        ["dashboard/users", () => import("./admin-overview/DashboardUserPage")],
        ["system-tasks", () => import("./admin-overview/SystemTasksPage")],
    ]],

    ["blueprints/instances", () => import("./blueprints/BlueprintListPage")],

    ["core", [
        ["providers", () => import("./providers/ProviderListPage")],
        [`providers/(?<providerID>${id})`, () => import("./providers/ProviderViewPage")],

        ["applications", () => import("./applications/ApplicationListPage")],
        [`applications/(?<applicationSlug>${slug})`, () => import("./applications/ApplicationViewPage")],

        ["sources", () => import("./sources/SourceListPage")],
        [`sources/(?<sourceSlug>${slug})`, () => import("./sources/SourceViewPage")],

        ["property-mappings", () => import("./property-mappings/PropertyMappingListPage")],

        ["tokens", () => import("./tokens/TokenListPage")],
        ["brands", () => import("./brands/BrandListPage")],
    ]],

    ["crypto/certificates", () => import("./crypto/CertificateKeyPairListPage")],

    ["debug", () => import("./DebugPage")],

    ["endpoints", [
        ["devices", () => import("./endpoints/devices/DeviceListPage")],
        [`devices/(?<deviceID>${uuid})`, () => import("./endpoints/devices/DeviceViewPage")],

        ["connectors", () => import("./endpoints/connectors/ConnectorsListPage")],
        [`connectors/(?<connectorID>${uuid})`,() => import("./endpoints/connectors/ConnectorViewPage")],

        ["groups", () => import("./endpoints/DeviceAccessGroupsListPage")],
    ]],

    ["enterprise/licenses", () => import("./enterprise/EnterpriseLicenseListPage")],

    ["events", [
        ["log", () => import("./events/EventListPage")],
        [`log/(?<eventID>${uuid})`, () => import("./events/EventViewPage")],

        ["transports", () => import("./events/TransportListPage")],

        ["rules", () => import("./events/RuleListPage")],

        ["exports", () => import("./events/DataExportListPage")],

        ["lifecycle-rules", () => import("./lifecycle/LifecycleRuleListPage")],
        ["lifecycle-reviews", () => import("./lifecycle/ReviewListPage")],
    ]],

    ["files", () => import("./files/FileListPage")],

    ["flow", [
        ["flows", () => import("./flows/FlowListPage")],
        [`flows/(?<flowSlug>${slug})`, () => import("./flows/FlowViewPage")],

        ["stages", () => import("./stages/StageListPage")],
        ["stages/invitations", () => import("./stages/invitation/InvitationListPage")],
        ["stages/prompts", () => import("./stages/prompt/PromptListPage")],
    ]],

    ["identity", [
        ["groups", () => import("./groups/GroupListPage")],
        [`groups/(?<groupID>${uuid})`, () => import("./groups/GroupViewPage")],

        ["users", () => import("./users/UserListPage")],
        [`users/(?<userID>${id})`, () => import("./users/UserViewPage")],

        ["roles", () => import("./roles/RoleListPage")],
        [`roles/(?<roleID>${uuid})`, () => import("./roles/RoleViewPage")],
        ["initial-permissions", () => import("./rbac/InitialPermissionsListPage")],
    ]],

    ["outpost", [
        ["outposts", () => import("./outposts/OutpostListPage")],
        ["integrations", () => import("./outposts/ServiceConnectionListPage")],
    ]],

    ["policy", [
        ["policies", () => import("./policies/PolicyListPage")],
        ["reputation", () => import("./policies/reputation/ReputationListPage")],
    ]],
]);

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
