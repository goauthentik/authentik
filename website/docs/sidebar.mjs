/**
 * @file Sidebar configuration for documentation entries.
 *
 * @import { SidebarItemConfig } from "@docusaurus/plugin-content-docs/src/sidebars/types.js"
 */

import * as path from "node:path";
import { fileURLToPath } from "node:url";

import {
    collectReleaseFiles,
    createReleaseSidebarEntries,
} from "@goauthentik/docusaurus-theme/releases/utils";

const __dirname = fileURLToPath(new URL(".", import.meta.url));

const releases = collectReleaseFiles(path.join(__dirname));

/**
 * @type {SidebarItemConfig[]}
 */
const items = [
    {
        type: "doc",
        id: "index",
    },
    {
        //#region Core Concepts
        type: "category",
        label: "Core Concepts",
        collapsed: true,
        items: ["core/terminology", "core/architecture"],
    },
    {
        //#endregion

        //#region Enterprise
        type: "category",
        label: "Enterprise",
        collapsed: true,
        link: {
            type: "doc",
            id: "enterprise/index",
        },
        items: ["enterprise/get-started", "enterprise/manage-enterprise", "enterprise/entsupport"],
    },
    {
        //#endregion

        //#region Installation and Configuration
        type: "category",
        label: "Installation and Configuration ",
        collapsed: true,
        link: {
            type: "doc",
            id: "install-config/index",
        },
        items: [
            {
                //#endregion

                //#region Installation
                type: "category",
                label: "Installation",
                collapsed: true,
                items: [
                    "install-config/install/docker-compose",
                    "install-config/install/kubernetes",
                    "install-config/install/aws",
                ],
            },
            {
                //#endregion

                //#region Configuration
                type: "category",
                label: "Configuration",
                link: {
                    type: "doc",
                    id: "install-config/configuration/configuration",
                },
                items: [],
            },
            "install-config/upgrade",
            "install-config/beta",
            "install-config/reverse-proxy",
            "install-config/automated-install",
            "install-config/air-gapped",
        ],
    },
    {
        //#endregion

        //#region Add and Secure Applications
        type: "category",
        label: "Add and Secure Applications",
        collapsed: true,
        items: [
            {
                //#endregion

                //#region Applications
                type: "category",
                label: "Applications",
                link: {
                    type: "doc",
                    id: "add-secure-apps/applications/index",
                },
                items: ["add-secure-apps/applications/manage_apps"],
            },
            {
                //#endregion

                //#region Providers
                type: "category",
                label: "Providers",
                link: {
                    type: "doc",
                    id: "add-secure-apps/providers/index",
                },
                items: [
                    {
                        type: "category",
                        label: "Property Mappings",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/providers/property-mappings/index",
                        },
                        items: ["add-secure-apps/providers/property-mappings/expression"],
                    },
                    {
                        type: "category",
                        label: "Google Workspace Provider",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/providers/gws/index",
                        },
                        items: [
                            "add-secure-apps/providers/gws/setup-gws",
                            "add-secure-apps/providers/gws/add-gws-provider",
                        ],
                    },
                    {
                        type: "category",
                        label: "LDAP Provider",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/providers/ldap/index",
                        },
                        items: ["add-secure-apps/providers/ldap/generic_setup"],
                    },
                    {
                        type: "category",
                        label: "Microsoft Entra ID Provider",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/providers/entra/index",
                        },
                        items: [
                            "add-secure-apps/providers/entra/setup-entra",
                            "add-secure-apps/providers/entra/add-entra-provider",
                        ],
                    },
                    {
                        type: "category",
                        label: "OAuth2 Provider",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/providers/oauth2/index",
                        },
                        items: [
                            "add-secure-apps/providers/oauth2/create-oauth2-provider",
                            "add-secure-apps/providers/oauth2/client_credentials",
                            "add-secure-apps/providers/oauth2/device_code",
                            "add-secure-apps/providers/oauth2/github-compatibility",
                            "add-secure-apps/providers/oauth2/webfinger_support",
                        ],
                    },
                    {
                        type: "category",
                        label: "Proxy Provider",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/providers/proxy/index",
                        },
                        items: [
                            "add-secure-apps/providers/proxy/custom_headers",
                            "add-secure-apps/providers/proxy/header_authentication",
                            {
                                type: "category",
                                label: "Forward authentication",
                                link: {
                                    type: "doc",
                                    id: "add-secure-apps/providers/proxy/forward_auth",
                                },
                                items: [
                                    "add-secure-apps/providers/proxy/server_nginx",
                                    "add-secure-apps/providers/proxy/server_traefik",
                                    "add-secure-apps/providers/proxy/server_envoy",
                                    "add-secure-apps/providers/proxy/server_caddy",
                                ],
                            },
                        ],
                    },
                    {
                        type: "category",
                        label: "RAC (Remote Access Control) Provider",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/providers/rac/index",
                        },
                        items: [
                            "add-secure-apps/providers/rac/how-to-rac",
                            "add-secure-apps/providers/rac/rac-public-key",
                            "add-secure-apps/providers/rac/rac_credentials_prompt",
                        ],
                    },
                    "add-secure-apps/providers/radius/index",
                    "add-secure-apps/providers/saml/index",
                    "add-secure-apps/providers/scim/index",
                    {
                        type: "category",
                        label: "SSF Provider",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/providers/ssf/index",
                        },
                        items: ["add-secure-apps/providers/ssf/create-ssf-provider"],
                    },
                ],
            },
            {
                //#endregion

                //#region Flows and Stages
                type: "category",
                label: "Flows and Stages",
                collapsed: true,
                items: [
                    {
                        type: "category",
                        label: "Flows",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/flows-stages/flow/index",
                        },
                        items: [
                            "add-secure-apps/flows-stages/flow/inspector",
                            "add-secure-apps/flows-stages/flow/context/index",
                            {
                                type: "category",
                                label: "Defaults and Examples",
                                items: [
                                    "add-secure-apps/flows-stages/flow/examples/flows",
                                    "add-secure-apps/flows-stages/flow/examples/default_flows",
                                    "add-secure-apps/flows-stages/flow/examples/snippets",
                                ],
                            },
                            {
                                type: "category",
                                label: "Executors",
                                items: [
                                    "add-secure-apps/flows-stages/flow/executors/if-flow",
                                    "add-secure-apps/flows-stages/flow/executors/sfe",
                                    "add-secure-apps/flows-stages/flow/executors/user-settings",
                                    "add-secure-apps/flows-stages/flow/executors/headless",
                                ],
                            },
                        ],
                    },
                    {
                        type: "category",
                        label: "Stages",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/flows-stages/stages/index",
                        },
                        items: [
                            "add-secure-apps/flows-stages/stages/authenticator_duo/index",
                            "add-secure-apps/flows-stages/stages/authenticator_email/index",
                            "add-secure-apps/flows-stages/stages/authenticator_endpoint_gdtc/index",
                            "add-secure-apps/flows-stages/stages/authenticator_sms/index",
                            "add-secure-apps/flows-stages/stages/authenticator_static/index",
                            "add-secure-apps/flows-stages/stages/authenticator_totp/index",
                            "add-secure-apps/flows-stages/stages/authenticator_validate/index",
                            "add-secure-apps/flows-stages/stages/authenticator_webauthn/index",
                            "add-secure-apps/flows-stages/stages/captcha/index",
                            "add-secure-apps/flows-stages/stages/deny",
                            "add-secure-apps/flows-stages/stages/email/index",
                            "add-secure-apps/flows-stages/stages/identification/index",
                            "add-secure-apps/flows-stages/stages/invitation/index",
                            "add-secure-apps/flows-stages/stages/mtls/index",
                            "add-secure-apps/flows-stages/stages/password/index",
                            "add-secure-apps/flows-stages/stages/prompt/index",
                            "add-secure-apps/flows-stages/stages/redirect/index",
                            "add-secure-apps/flows-stages/stages/source/index",
                            "add-secure-apps/flows-stages/stages/user_delete",
                            "add-secure-apps/flows-stages/stages/user_login/index",
                            "add-secure-apps/flows-stages/stages/user_logout",
                            "add-secure-apps/flows-stages/stages/user_write",
                        ],
                    },
                    {
                        type: "category",
                        label: "Bindings",
                        link: {
                            type: "doc",
                            id: "add-secure-apps/flows-stages/bindings/index",
                        },
                        items: ["add-secure-apps/flows-stages/bindings/work_with_bindings"],
                    },
                ],
            },
            {
                //#endregion

                //#region Outposts
                type: "category",
                label: "Outposts",
                link: {
                    type: "doc",
                    id: "add-secure-apps/outposts/index",
                },
                items: [
                    "add-secure-apps/outposts/embedded/embedded",
                    {
                        type: "category",
                        label: "Integrations",
                        items: [
                            "add-secure-apps/outposts/integrations/docker",
                            "add-secure-apps/outposts/integrations/kubernetes",
                        ],
                    },
                    {
                        type: "category",
                        label: "Running and upgrading",
                        items: [
                            "add-secure-apps/outposts/manual-deploy-docker-compose",
                            "add-secure-apps/outposts/manual-deploy-kubernetes",
                            "add-secure-apps/outposts/upgrading",
                        ],
                    },
                    "add-secure-apps/outposts/manual-deploy-docker-compose",
                    "add-secure-apps/outposts/manual-deploy-kubernetes",
                ],
            },
        ],
    },
    {
        //#endregion

        //#region Customize your instance
        type: "category",
        label: "Customize your instance",
        collapsed: true,
        link: {
            type: "doc",
            id: "customize/index",
        },
        items: [
            {
                //#endregion

                //#region Policies
                type: "category",
                label: "Policies",
                collapsed: true,
                link: {
                    type: "doc",
                    id: "customize/policies/index",
                },
                items: [
                    "customize/policies/working_with_policies",
                    {
                        type: "category",
                        label: "Expression Policies",
                        link: {
                            type: "doc",
                            id: "customize/policies/expression",
                        },
                        items: [
                            "customize/policies/expression/unique_email",
                            "customize/policies/expression/whitelist_email",
                            "customize/policies/expression/managing_flow_context_keys",
                        ],
                    },
                    "customize/policies/unique_password",
                ],
            },
            {
                //#endregion

                //#region Interfaces
                type: "category",
                label: "Interfaces",
                items: [
                    "customize/interfaces/flow/index",
                    "customize/interfaces/user/index",
                    "customize/interfaces/admin/index",
                ],
            },
            {
                //#endregion

                //#region Blueprints
                type: "category",
                label: "Blueprints",
                link: {
                    type: "doc",
                    id: "customize/blueprints/index",
                },
                items: [
                    "customize/blueprints/export",
                    "customize/blueprints/v1/structure",
                    "customize/blueprints/v1/tags",
                    "customize/blueprints/v1/example",
                    {
                        type: "category",
                        label: "Models",
                        link: {
                            type: "doc",
                            id: "customize/blueprints/v1/models",
                        },
                        items: ["customize/blueprints/v1/meta"],
                    },
                ],
            },
            "customize/branding",
        ],
    },
    {
        //#endregion

        //#region Manage Users and Sources
        type: "category",
        label: "Manage Users and Sources",
        collapsed: true,
        items: [
            {
                //#endregion

                //#region Users
                type: "category",
                label: "Users",
                link: {
                    type: "doc",
                    id: "users-sources/user/index",
                },
                items: [
                    "users-sources/user/user_basic_operations",
                    "users-sources/user/user_ref",
                    "users-sources/user/invitations",
                    "users-sources/user/password_reset_on_login",
                ],
            },
            {
                //#endregion

                //#region Groups
                type: "category",
                label: "Groups",
                link: {
                    type: "doc",
                    id: "users-sources/groups/index",
                },
                items: ["users-sources/groups/manage_groups", "users-sources/groups/group_ref"],
            },
            {
                //#endregion

                //#region Roles
                type: "category",
                label: "Roles",
                link: {
                    type: "doc",
                    id: "users-sources/roles/index",
                },
                items: ["users-sources/roles/manage_roles"],
            },
            {
                //#endregion

                //#region Access Control
                type: "category",
                label: "Access Control",
                link: {
                    type: "doc",
                    id: "users-sources/access-control/index",
                },
                items: [
                    "users-sources/access-control/permissions",
                    "users-sources/access-control/manage_permissions",
                    "users-sources/access-control/initial_permissions",
                ],
            },
            {
                //#endregion

                //#region Federated and Social Sources
                type: "category",
                label: "Federated and Social Sources",
                collapsed: true,
                link: {
                    type: "doc",
                    id: "users-sources/sources/index",
                },
                items: [
                    {
                        type: "category",
                        label: "Protocols",
                        collapsed: true,
                        items: [
                            {
                                type: "category",
                                label: "Kerberos",
                                link: {
                                    type: "doc",
                                    id: "users-sources/sources/protocols/kerberos/index",
                                },
                                items: ["users-sources/sources/protocols/kerberos/browser"],
                            },
                            "users-sources/sources/protocols/ldap/index",
                            "users-sources/sources/protocols/oauth/index",
                            "users-sources/sources/protocols/saml/index",
                            "users-sources/sources/protocols/scim/index",
                        ],
                    },
                    {
                        type: "category",
                        label: "Source Property Mappings",
                        link: {
                            type: "doc",
                            id: "users-sources/sources/property-mappings/index",
                        },
                        items: ["users-sources/sources/property-mappings/expressions"],
                    },
                    {
                        type: "category",
                        label: "Directory synchronization",
                        items: [
                            "users-sources/sources/directory-sync/active-directory/index",
                            "users-sources/sources/directory-sync/freeipa/index",
                        ],
                    },
                    {
                        type: "category",
                        label: "Identity Providers",
                        link: {
                            type: "doc",
                            id: "users-sources/sources/social-logins/index",
                        },
                        items: [
                            "users-sources/sources/social-logins/apple/index",
                            "users-sources/sources/social-logins/azure-ad/index",
                            "users-sources/sources/social-logins/discord/index",
                            "users-sources/sources/social-logins/facebook/index",
                            "users-sources/sources/social-logins/github/index",
                            {
                                type: "category",
                                label: "Google",
                                link: {
                                    type: "doc",
                                    id: "users-sources/sources/social-logins/google/index",
                                },
                                items: [
                                    "users-sources/sources/social-logins/google/cloud/index",
                                    "users-sources/sources/social-logins/google/workspace/index",
                                ],
                            },
                            "users-sources/sources/social-logins/mailcow/index",
                            "users-sources/sources/social-logins/plex/index",
                            "users-sources/sources/social-logins/telegram/index",
                            "users-sources/sources/social-logins/twitch/index",
                            "users-sources/sources/social-logins/twitter/index",
                        ],
                    },
                ],
            },
        ],
    },
    {
        //#endregion

        //#region System Management
        type: "category",
        label: "System Management",
        collapsed: true,
        items: [
            "sys-mgmt/background-tasks",
            "sys-mgmt/brands",
            {
                //#endregion

                //#region Operations
                type: "category",
                label: "Operations",
                collapsed: true,
                items: [
                    "sys-mgmt/ops/monitoring",
                    "sys-mgmt/ops/worker",
                    "sys-mgmt/ops/storage-s3",
                    "sys-mgmt/ops/geoip",
                    "sys-mgmt/ops/backup-restore",
                ],
            },
            {
                //#endregion

                //#region Events
                type: "category",
                label: "Events",
                collapsed: true,
                link: {
                    type: "doc",
                    id: "sys-mgmt/events/index",
                },
                items: [
                    "sys-mgmt/events/notifications",
                    "sys-mgmt/events/transports",
                    "sys-mgmt/events/logging-events",
                    "sys-mgmt/events/event-actions",
                ],
            },
            "sys-mgmt/certificates",
            "sys-mgmt/settings",
            "sys-mgmt/service-accounts",
        ],
    },
    {
        //#endregion

        //#region Developer Documentation
        type: "category",
        label: "Developer Documentation",
        collapsed: true,
        link: {
            type: "doc",
            id: "developer-docs/index",
        },
        items: [
            {
                type: "link",
                href: "https://api.goauthentik.io",
                label: "API Overview",
                className: "api-overview",
            },

            {
                //#endregion

                //#region Development environment
                type: "category",
                label: "Development environment",
                items: [
                    "developer-docs/setup/full-dev-environment",
                    "developer-docs/setup/frontend-dev-environment",
                    "developer-docs/setup/website-dev-environment",
                    "developer-docs/setup/debugging",
                ],
            },
            {
                //#endregion

                //#region Writing documentation
                type: "category",
                label: "Writing documentation",
                link: {
                    type: "doc",
                    id: "developer-docs/docs/writing-documentation",
                },
                items: [
                    "developer-docs/docs/style-guide",
                    {
                        type: "category",
                        label: "Templates",
                        link: {
                            type: "doc",
                            id: "developer-docs/docs/templates/index",
                        },
                        items: [
                            "developer-docs/docs/templates/procedural",
                            "developer-docs/docs/templates/conceptual",
                            "developer-docs/docs/templates/reference",
                            "developer-docs/docs/templates/combo",
                        ],
                    },
                ],
            },
            {
                type: "doc",
                id: "developer-docs/releases/index",
            },
            "developer-docs/translation",
        ],
    },
    {
        //#endregion

        //#region Security
        type: "category",
        label: "Security",
        collapsed: true,
        link: {
            type: "generated-index",
            title: "Security",
            slug: "security",
        },
        items: [
            "security/policy",
            "security/security-hardening",
            {
                //#endregion

                //#region Audits and Certificates
                type: "category",
                label: "Audits and Certificates",
                items: [
                    "security/audits-and-certs/2023-06-cure53",
                    "security/audits-and-certs/2024-11-cobalt",
                ],
            },
            {
                //#endregion

                //#region CVEs
                type: "category",
                label: "CVEs",
                items: [
                    {
                        type: "category",
                        label: "2025",
                        items: [
                            "security/cves/CVE-2025-53942",
                            "security/cves/CVE-2025-52553",
                            "security/cves/CVE-2025-29928",
                        ],
                    },
                    {
                        type: "category",
                        label: "2024",
                        items: [
                            "security/cves/CVE-2024-52307",
                            "security/cves/CVE-2024-52289",
                            "security/cves/CVE-2024-52287",
                            "security/cves/CVE-2024-47077",
                            "security/cves/CVE-2024-47070",
                            "security/cves/CVE-2024-42490",
                            "security/cves/CVE-2024-38371",
                            "security/cves/CVE-2024-37905",
                            "security/cves/CVE-2024-23647",
                            "security/cves/CVE-2024-21637",
                        ],
                    },
                    {
                        type: "category",
                        label: "2023",
                        items: [
                            "security/cves/CVE-2023-48228",
                            "security/cves/GHSA-rjvp-29xq-f62w",
                            "security/cves/CVE-2023-39522",
                            "security/cves/CVE-2023-36456",
                            "security/cves/CVE-2023-26481",
                        ],
                    },
                    {
                        type: "category",
                        label: "2022",
                        items: [
                            "security/cves/CVE-2022-46172",
                            "security/cves/CVE-2022-46145",
                            "security/cves/CVE-2022-23555",
                        ],
                    },
                ],
            },
        ],
    },
    {
        //#endregion

        //#region Troubleshooting
        type: "category",
        label: "Troubleshooting",
        link: {
            type: "generated-index",
            title: "Troubleshooting",
            slug: "troubleshooting",
            description: "Troubleshooting various issues",
        },
        items: [
            {
                //#endregion

                //#region Forward auth
                type: "category",
                label: "Forward auth",
                items: ["troubleshooting/forward_auth/general"],
                link: {
                    type: "generated-index",
                    title: "Forward auth troubleshooting",
                    slug: "troubleshooting/forward_auth",
                    description:
                        "Steps to help debug forward auth setups with various reverse proxies.",
                },
            },
            {
                //#endregion

                //#region PostgreSQL
                type: "category",
                label: "PostgreSQL",
                items: [
                    "troubleshooting/postgres/upgrade_kubernetes",
                    "troubleshooting/postgres/upgrade_docker",
                ],
            },
            "troubleshooting/access",
            "troubleshooting/login",
            "troubleshooting/logs",
            "troubleshooting/image_upload",
            "troubleshooting/missing_permission",
            "troubleshooting/missing_admin_group",
            "troubleshooting/csrf",
            "troubleshooting/emails",
            "troubleshooting/ldap_source",
        ],
    },
    {
        //#endregion

        //#region Release Notes
        type: "category",
        label: "Release Notes",
        link: {
            type: "generated-index",
            title: "Releases",
            slug: "releases",
            description: "Release Notes for recent authentik versions",
        },
        items: createReleaseSidebarEntries(releases),
    },
];

/**
 * @type {SidebarItemConfig}
 */
const sidebar = {
    docs: items,
};

export default sidebar;
