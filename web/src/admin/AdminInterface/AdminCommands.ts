import { navigate } from "@goauthentik/elements/router/RouterOutlet";
import { INinjaAction } from "ninja-keys/dist/interfaces/ininja-action.js";

import { msg } from "@lit/localize";

export const adminCommands: INinjaAction[] = [
    {
        id: msg("Overview"),
        title: msg("Dashboard"),
        handler: () => navigate("/administration/overview"),
        section: msg("Dashboards"),
    },
    {
        handler: () => navigate("/administration/dashboard/users"),
        id: msg("User Statistics"),
        title: msg("User Statistics"),
        icon: '<i class="pf-icon pf-icon-user"></i>',
        section: msg("Dashboards"),
    },
    {
        handler: () => navigate("/administration/system-tasks"),
        id: msg("System Tasks"),
        title: msg("System Tasks"),
        section: msg("Dashboards"),
    },
    {
        handler: () => navigate("/core/applications"),
        id: msg("Applications"),
        title: msg("Applications"),
        section: msg("Applications"),
    },
    {
        handler: () => navigate("/core/providers"),
        id: msg("Providers"),
        title: msg("Providers"),
        section: msg("Applications"),
    },
    {
        handler: () => navigate("/outpost/outposts"),
        id: msg("Outposts"),
        title: msg("Outposts"),
        section: msg("Applications"),
    },
    {
        handler: () => navigate("/events/log"),
        id: msg("Logs"),
        title: msg("Logs"),
        section: msg("Events"),
    },
    {
        handler: () => navigate("/events/rules"),
        id: msg("Notification Rules"),
        title: msg("Notification Rules"),
        section: msg("Events"),
    },
    {
        handler: () => navigate("/events/transports"),
        id: msg("Notification Transports"),
        title: msg("Notification Transports"),
        section: msg("Events"),
    },

    {
        handler: () => navigate("/policy/policies"),
        id: msg("Policies"),
        title: msg("Policies"),
        section: msg("Customization"),
    },
    {
        handler: () => navigate("/core/property-mappings"),
        id: msg("Property Mappings"),
        title: msg("Property Mappings"),
        section: msg("Customization"),
    },
    {
        handler: () => navigate("/blueprints/instances"),
        id: msg("Blueprints"),
        title: msg("Blueprints"),
        section: msg("Customization"),
    },
    {
        handler: () => navigate("/policy/reputation"),
        id: msg("Reputation scores"),
        title: msg("Reputation scores"),
        section: msg("Customization"),
    },
    {
        handler: () => navigate("/flow/flows"),
        id: msg("Flows"),
        title: msg("Flows"),
        section: msg("Flows"),
    },
    {
        handler: () => navigate("/flow/stages"),
        id: msg("Stages"),
        title: msg("Stages"),
        section: msg("Flows"),
    },
    {
        handler: () => navigate("/flow/stages/prompts"),
        id: msg("Prompts"),
        title: msg("Prompts"),
        section: msg("Flows"),
    },

    {
        handler: () => navigate("/identity/users"),
        id: msg("Users"),
        title: msg("Users"),
        section: msg("Directory"),
    },
    {
        handler: () => navigate("/identity/groups"),
        id: msg("Groups"),
        title: msg("Groups"),
        section: msg("Directory"),
    },
    {
        handler: () => navigate("/identity/roles"),
        id: msg("Roles"),
        title: msg("Roles"),
        section: msg("Directory"),
    },
    {
        handler: () => navigate("/core/sources"),
        id: msg("Federation and Social login"),
        title: msg("Federation and Social login"),
        section: msg("Directory"),
    },
    {
        handler: () => navigate("/core/tokens"),
        id: msg("Tokens and App passwords"),
        title: msg("Tokens and App passwords"),
        section: msg("Directory"),
    },
    {
        handler: () => navigate("/flow/stages/invitations"),
        id: msg("Invitations"),
        title: msg("Invitations"),
        section: msg("Directory"),
    },

    {
        handler: () => navigate("/core/brands"),
        id: msg("Brands"),
        title: msg("Brands"),
        section: msg("System"),
    },
    {
        handler: () => navigate("/crypto/certificates"),
        id: msg("Certificates"),
        title: msg("Certificates"),
        section: msg("System"),
    },
    {
        handler: () => navigate("/outpost/integrations"),
        id: msg("Outpost Integrations"),
        title: msg("Outpost Integrations"),
        section: msg("System"),
    },
    {
        handler: () => navigate("/admin/settings"),
        id: msg("Settings"),
        title: msg("Settings"),
        section: msg("System"),
    },
    {
        handler: () => window.location.assign("/if/user/"),
        id: msg("User interface"),
        title: msg("Go to my User page"),
    },
];
