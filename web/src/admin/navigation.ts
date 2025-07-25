import { toAdminRoute } from "#elements/router/navigation";

export const toAdministrationDashboardUsers = () => toAdminRoute("/administration/dashboard/users");

export const toAdministrationOverview = () => toAdminRoute("/administration/overview");

export const toAdministrationSystemTasks = () => toAdminRoute("/administration/system-tasks");

export const toAdminSettings = () => toAdminRoute("/admin/settings");

export const toApplication = (slug: string) => toAdminRoute(`/core/applications/${slug}`);

export const toApplications = (params?: { createWizard?: boolean }) => {
    return toAdminRoute(`/core/applications`, params);
};

export const toBlueprintsInstances = () => toAdminRoute("/blueprints/instances");

export const toBrands = () => toAdminRoute("/core/brands");

export const toPropertyMappings = () => toAdminRoute("/core/property-mappings");

export const toSources = () => toAdminRoute("/core/sources");

export const toTokens = () => toAdminRoute("/core/tokens");

export const toCryptoCertificates = () => toAdminRoute("/crypto/certificates");

export const toEnterpriseLicenses = () => toAdminRoute("/enterprise/licenses");

export const toEventLog = (id: string) => toAdminRoute(`/events/log/${id}`);

export const toEventLogs = () => toAdminRoute("/events/log");

export const toEventsRules = () => toAdminRoute("/events/rules");

export const toEventsTransports = () => toAdminRoute("/events/transports");

export const toFlow = (slug: string) => toAdminRoute(`/flow/flows/${slug}`);

export const toFlows = () => toAdminRoute("/flow/flows");

export const toFlowStages = () => toAdminRoute("/flow/stages");

export const toFlowStagesInvitations = () => toAdminRoute("/flow/stages/invitations");

export const toFlowStagesPrompts = () => toAdminRoute("/flow/stages/prompts");

export const toIdentityGroup = (id: string) => toAdminRoute(`/identity/groups/${id}`);

export const toIdentityGroups = () => toAdminRoute("/identity/groups");

export const toIdentityInitialPermissions = () => toAdminRoute("/identity/initial-permissions");

export const toIdentityRole = (id: string) => toAdminRoute(`/identity/roles/${id}`);

export const toIdentityRoles = () => toAdminRoute("/identity/roles");

export const toIdentityUser = (id: number) => toAdminRoute(`/identity/users/${id}`);

export const toIdentityUsers = () => toAdminRoute("/identity/users");

export const toOutpostIntegrations = () => toAdminRoute("/outpost/integrations");

export const toOutposts = () => toAdminRoute("/outpost/outposts");

export const toPolicyPolicies = () => toAdminRoute("/policy/policies");

export const toPolicyReputation = () => toAdminRoute("/policy/reputation");

export const toProvider = (id: number) => toAdminRoute(`/core/providers/${id}`);

export const toProviders = () => toAdminRoute(`/core/providers`);

export const toSource = (slug: string) => toAdminRoute(`/core/sources/${slug}`);
