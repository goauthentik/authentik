const generateVersionDropdown =
    require("./src/utils.js").generateVersionDropdown;

const docsSidebar = {
    docs: [
        {
            type: "html",
        },
        {
            type: "doc",
            id: "index",
        },
        {
            type: "category",
            label: "Core Concepts",
            collapsed: true,
            items: ["core/terminology", "core/architecture"],
        },
        {
            type: "category",
            label: "Enterprise",
            collapsed: true,
            link: {
                type: "doc",
                id: "enterprise/index",
            },
            items: [
                "enterprise/get-started",
                "enterprise/manage-enterprise",
                "enterprise/entsupport",
            ],
        },
        {
            type: "category",
            label: "Installation and Configuration ",
            collapsed: true,
            link: {
                type: "doc",
                id: "install-config/index",
            },
            items: [
                {
                    type: "category",
                    label: "Installation",
                    link: {
                        type: "doc",
                        id: "install-config/install/index",
                    },
                    items: [
                        "install-config/install/docker-compose",
                        "install-config/install/kubernetes",
                    ],
                },
                {
                    type: "category",
                    label: "Configuration",
                    link: {
                        type: "doc",
                        id: "install-config/configuration/configuration",
                    },
                },
                "install-config/upgrade",
                "install-config/beta",
                "install-config/reverse-proxy",
                "install-config/geoip",
                "install-config/automated-install",
                "install-config/air-gapped",
                "install-config/monitoring",
                "install-config/storage-s3",
            ],
        },
        {
            type: "category",
            label: "Add and Secure Applications",
            collapsed: true,
            link: {
                type: "doc",
                id: "add-secure-apps/index",
            },
            items: [
                {
                    type: "category",
                    label: "Applications",
                    items: ["add-secure-apps/applications/manage_apps"],
                },
                {
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
                            items: [
                                "add-secure-apps/providers/property-mappings/expression",
                            ],
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
                            items: [
                                "add-secure-apps/providers/ldap/generic_setup",
                            ],
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
                                "add-secure-apps/providers/oauth2/client_credentials",
                                "add-secure-apps/providers/oauth2/device_code",
                            ],
                        },
                        "add-secure-apps/providers/saml/index",
                        "add-secure-apps/providers/radius/index",
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
                        "add-secure-apps/providers/scim/index",
                        {
                            type: "category",
                            label: "RAC (Remote Access Control) Provider",
                            link: {
                                type: "doc",
                                id: "add-secure-apps/providers/rac/index",
                            },
                            items: ["add-secure-apps/providers/rac/how-to-rac"],
                        },
                    ],
                },
                {
                    type: "category",
                    label: "Flows and Stages",
                    link: {
                        type: "doc",
                        id: "add-secure-apps/flows-stages/index",
                    },
                    items: [
                        {
                            type: "category",
                            label: "Flows",
                            link: {
                                type: "doc",
                                id: "add-secure-apps/flows-stages/flow/index",
                            },
                            items: [
                                "add-secure-apps/flows-stages/flow/layouts",
                                "add-secure-apps/flows-stages/flow/inspector",
                                "add-secure-apps/flows-stages/flow/context/index",
                            ],
                        },
                        {
                            type: "category",
                            label: "Examples",
                            items: [
                                "add-secure-apps/flows-stages/flow/examples/flows",
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
                        {
                            type: "category",
                            label: "Stages",
                            link: {
                                type: "doc",
                                id: "add-secure-apps/flows-stages/stages/index",
                            },
                            items: [
                                "add-secure-apps/flows-stages/stages/authenticator_duo/index",
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
                                "add-secure-apps/flows-stages/stages/password/index",
                                "add-secure-apps/flows-stages/stages/prompt/index",
                                "add-secure-apps/flows-stages/stages/source/index",
                                "add-secure-apps/flows-stages/stages/user_delete",
                                "add-secure-apps/flows-stages/stages/user_login/index",
                                "add-secure-apps/flows-stages/stages/user_logout",
                                "add-secure-apps/flows-stages/stages/user_write",
                            ],
                        },
                    ],
                },
                {
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
                        "add-secure-apps/outposts/manual-deploy-docker-compose.md",
                        "add-secure-apps/outposts/manual-deploy-kubernetes",
                    ],
                },
            ],
        },
        {
            type: "category",
            label: "Customize your authentik Instance",
            collapsed: true,
            link: {
                type: "doc",
                id: "customize/index",
            },
            items: [
                {
                    type: "category",
                    label: "Policies",
                    collapsed: true,
                    link: {
                        type: "doc",
                        id: "customize/policies/index",
                    },
                    items: [
                        {
                            type: "category",
                            label: "Working with Policies",
                            link: {
                                type: "doc",
                                id: "customize/policies/working_with_policies/working_with_policies",
                            },
                            items: [
                                "customize/policies/working_with_policies/unique_email",
                                "customize/policies/working_with_policies/whitelist_email",
                            ],
                        },
                    ],
                },
                {
                    type: "category",
                    label: "Interfaces",
                    items: [
                        {
                            type: "category",
                            label: "Flow",
                            items: ["customize/interfaces/flow/customization"],
                        },
                        {
                            type: "category",
                            label: "User",
                            items: ["customize/interfaces/user/customization"],
                        },
                        {
                            type: "category",
                            label: "Admin",
                            items: ["customize/interfaces/admin/customization"],
                        },
                        "customize/brands",
                    ],
                },
            ],
        },
        {
            type: "category",
            label: "Manage Users and Sources",
            collapsed: true,
            link: {
                type: "doc",
                id: "users-sources/index",
            },
            items: [
                {
                    type: "category",
                    label: "Users",
                    link: {
                        type: "doc",
                        id: "user-sources/user/index",
                    },
                    items: [
                        "user-sources/user/user_basic_operations",
                        "user-sources/user/user_ref",
                        "user-sources/user/invitations",
                    ],
                },
                {
                    type: "category",
                    label: "Groups",
                    link: {
                        type: "doc",
                        id: "user-sources/groups/index",
                    },
                    items: [
                        "user-sources/groups/manage_groups",
                        "user-sources/groups/group_ref",
                    ],
                },
                {
                    type: "category",
                    label: "Roles",
                    link: {
                        type: "doc",
                        id: "user-sources/roles/index",
                    },
                    items: ["user-sources/roles/manage_roles"],
                },
                {
                    type: "category",
                    label: "Access Control",
                    link: {
                        type: "doc",
                        id: "user-sources/access-control/index",
                    },
                    items: [
                        "user-sources/access-control/permissions",
                        "user-sources/access-control/manage_permissions",
                    ],
                },
                {
                    type: "category",
                    label: "Federated and Social Sources",
                    collapsed: true,
                    link: {
                        type: "doc",
                        id: "user-sources/sources/index",
                    },
                    items: [
                        {
                            type: "category",
                            label: "Protocols",
                            collapsed: true,
                            items: [
                                "user-sources/sources/protocols/ldap/index",
                                "user-sources/sources/protocols/oauth/index",
                                "user-sources/sources/protocols/saml/index",
                                "user-sources/sources/protocols/scim/index",
                            ],
                        },
                        {
                            type: "category",
                            label: "Source Property Mappings",
                            link: {
                                type: "doc",
                                id: "user-sources/sources/property-mappings/index",
                            },
                            items: [
                                "user-sources/sources/property-mappings/expressions",
                            ],
                        },
                        {
                            type: "category",
                            label: "Directory synchronization",
                            items: [
                                "user-sources/sources/directory-sync/active-directory/index",
                                "user-sources/sources/directory-sync/freeipa/index",
                            ],
                        },
                        {
                            type: "category",
                            label: "Social Logins",
                            items: [
                                "user-sources/sources/social-logins/apple/index",
                                "user-sources/sources/social-logins/azure-ad/index",
                                "user-sources/sources/social-logins/discord/index",
                                "user-sources/sources/social-logins/facebook/index",
                                "user-sources/sources/social-logins/github/index",
                                "user-sources/sources/social-logins/google/index",
                                "user-sources/sources/social-logins/mailcow/index",
                                "user-sources/sources/social-logins/twitch/index",
                                "user-sources/sources/social-logins/plex/index",
                                "user-sources/sources/social-logins/twitter/index",
                            ],
                        },
                    ],
                },
            ],
        },
        {
            type: "category",
            label: "System Management",
            collapsed: true,
            link: {
                type: "doc",
                id: "sys-mgmt/index",
            },
            items: [
                {
                    type: "category",
                    label: "Operations",
                    collapsed: true,
                    link: {
                        type: "doc",
                        id: "sys-mgmt/ops/index",
                    },
                    items: ["sys-mgmt/ops/monitoring"],
                },
                {
                    type: "category",
                    label: "Events",
                    collapsed: true,
                    link: {
                        type: "doc",
                        id: "sys-mgmt/events/index",
                    },
                    items: ["events/notifications", "events/transports"],
                },
                "certificates",
                "settings",
            ],
        },
        {
            type: "category",
            label: "Security",
            link: {
                type: "generated-index",
                title: "Security",
                slug: "security",
            },
            items: [
                "security/security-hardening",
                "security/policy",
                "security/CVE-2024-38371",
                "security/CVE-2024-37905",
                "security/CVE-2024-23647",
                "security/CVE-2024-21637",
                "security/CVE-2023-48228",
                "security/GHSA-rjvp-29xq-f62w",
                "security/CVE-2023-39522",
                "security/CVE-2023-36456",
                "security/2023-06-cure53",
                "security/CVE-2023-26481",
                "security/CVE-2022-23555",
                "security/CVE-2022-46145",
                "security/CVE-2022-46172",
            ],
        },
        {
            type: "category",
            label: "Release Notes",
            link: {
                type: "generated-index",
                title: "Releases",
                slug: "releases",
                description: "Release Notes for recent authentik versions",
            },
            items: [
                "releases/2024/v2024.6",
                "releases/2024/v2024.4",
                "releases/2024/v2024.2",
                {
                    type: "category",
                    label: "Previous versions",
                    items: [
                        "releases/2023/v2023.10",
                        "releases/2023/v2023.8",
                        "releases/2023/v2023.6",
                        "releases/2023/v2023.5",
                        "releases/2023/v2023.4",
                        "releases/2023/v2023.3",
                        "releases/2023/v2023.2",
                        "releases/2023/v2023.1",
                        "releases/2022/v2022.12",
                        "releases/2022/v2022.11",
                        "releases/2022/v2022.10",
                        "releases/2022/v2022.9",
                        "releases/2022/v2022.8",
                        "releases/2022/v2022.7",
                        "releases/2022/v2022.6",
                        "releases/2022/v2022.5",
                        "releases/2022/v2022.4",
                        "releases/2022/v2022.2",
                        "releases/2022/v2022.1",
                        "releases/2021/v2021.12",
                        "releases/2021/v2021.10",
                        "releases/2021/v2021.9",
                        "releases/2021/v2021.8",
                        "releases/2021/v2021.7",
                        "releases/2021/v2021.6",
                        "releases/2021/v2021.5",
                        "releases/2021/v2021.4",
                        "releases/2021/v2021.3",
                        "releases/2021/v2021.2",
                        "releases/2021/v2021.1",
                        "releases/old/v0.14",
                        "releases/old/v0.13",
                        "releases/old/v0.12",
                        "releases/old/v0.11",
                        "releases/old/v0.10",
                        "releases/old/v0.9",
                    ],
                },
            ],
        },
    ],
};
docsSidebar.docs[0].value = generateVersionDropdown(docsSidebar);
module.exports = docsSidebar;
