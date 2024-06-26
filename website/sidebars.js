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
            label: "Installation",
            collapsed: true,
            link: {
                type: "doc",
                id: "installation/index",
            },
            items: [
                "installation/docker-compose",
                "installation/kubernetes",
                "installation/beta",
                "installation/configuration",
                "installation/reverse-proxy",
                "installation/automated-install",
                "installation/air-gapped",
                "installation/monitoring",
                "installation/storage-s3",
            ],
        },
        {
            type: "category",
            label: "Core Concepts & Tasks",
            collapsed: true,
            items: [
                "core/terminology",
                "core/brands",
                "core/certificates",
                "core/geoip",
                "core/architecture",
                "core/settings",
            ],
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
            label: "Applications",
            link: {
                type: "doc",
                id: "applications/index",
            },
            items: ["applications/manage_apps"],
        },
        {
            type: "category",
            label: "Providers",
            link: {
                type: "doc",
                id: "providers/index",
            },
            items: [
                {
                    type: "category",
                    label: "Google Workspace Provider",
                    link: {
                        type: "doc",
                        id: "providers/gws/index",
                    },
                    items: [
                        "providers/gws/setup-gws",
                        "providers/gws/add-gws-provider",
                    ],
                },
                {
                    type: "category",
                    label: "LDAP Provider",
                    link: {
                        type: "doc",
                        id: "providers/ldap/index",
                    },
                    items: ["providers/ldap/generic_setup"],
                },
                {
                    type: "category",
                    label: "Microsoft Entra ID Provider",
                    link: {
                        type: "doc",
                        id: "providers/entra/index",
                    },
                    items: [
                        "providers/entra/setup-entra",
                        "providers/entra/add-entra-provider",
                    ],
                },
                {
                    type: "category",
                    label: "OAuth2 Provider",
                    link: {
                        type: "doc",
                        id: "providers/oauth2/index",
                    },
                    items: [
                        "providers/oauth2/client_credentials",
                        "providers/oauth2/device_code",
                    ],
                },
                "providers/saml/index",
                "providers/radius/index",
                {
                    type: "category",
                    label: "Proxy Provider",
                    link: {
                        type: "doc",
                        id: "providers/proxy/index",
                    },
                    items: [
                        "providers/proxy/custom_headers",
                        "providers/proxy/header_authentication",
                        {
                            type: "category",
                            label: "Forward authentication",
                            link: {
                                type: "doc",
                                id: "providers/proxy/forward_auth",
                            },
                            items: [
                                "providers/proxy/server_nginx",
                                "providers/proxy/server_traefik",
                                "providers/proxy/server_envoy",
                                "providers/proxy/server_caddy",
                            ],
                        },
                    ],
                },
                "providers/scim/index",
                {
                    type: "category",
                    label: "RAC (Remote Access Control) Provider",
                    link: {
                        type: "doc",
                        id: "providers/rac/index",
                    },
                    items: ["providers/rac/how-to-rac"],
                },
            ],
        },
        {
            type: "category",
            label: "Sources",
            collapsed: true,
            link: {
                type: "doc",
                id: "sources/index",
            },
            items: [
                {
                    type: "category",
                    label: "Directory synchronization",
                    items: [
                        "sources/active-directory/index",
                        "sources/freeipa/index",
                    ],
                },
                {
                    type: "category",
                    label: "Protocols",
                    items: [
                        "sources/ldap/index",
                        "sources/oauth/index",
                        "sources/saml/index",
                        "sources/scim/index",
                    ],
                },
                {
                    type: "category",
                    label: "Social Logins",
                    items: [
                        "sources/apple/index",
                        "sources/azure-ad/index",
                        "sources/discord/index",
                        "sources/facebook/index",
                        "sources/github/index",
                        "sources/google/index",
                        "sources/mailcow/index",
                        "sources/twitch/index",
                        "sources/plex/index",
                        "sources/twitter/index",
                    ],
                },
            ],
        },
        {
            type: "category",
            label: "Outposts",
            link: {
                type: "doc",
                id: "outposts/index",
            },
            items: [
                "outposts/embedded/embedded",
                {
                    type: "category",
                    label: "Integrations",
                    items: [
                        "outposts/integrations/docker",
                        "outposts/integrations/kubernetes",
                    ],
                },
                {
                    type: "category",
                    label: "Running and upgrading",
                    items: [
                        "outposts/manual-deploy-docker-compose",
                        "outposts/manual-deploy-kubernetes",
                        "outposts/upgrading",
                    ],
                },
            ],
        },
        {
            type: "category",
            label: "Flows",
            link: {
                type: "doc",
                id: "flow/index",
            },
            items: [
                "flow/layouts",
                "flow/inspector",
                "flow/context/index",
                {
                    type: "category",
                    label: "Examples",
                    items: ["flow/examples/flows", "flow/examples/snippets"],
                },
                {
                    type: "category",
                    label: "Executors",
                    items: [
                        "flow/executors/if-flow",
                        "flow/executors/user-settings",
                        "flow/executors/headless",
                    ],
                },
            ],
        },
        {
            type: "category",
            label: "Stages",
            link: {
                type: "generated-index",
                title: "Stages",
                slug: "flow/stages",
                description: "Overview of all available stages",
            },
            items: [
                "flow/stages/authenticator_duo/index",
                "flow/stages/authenticator_sms/index",
                "flow/stages/authenticator_static/index",
                "flow/stages/authenticator_totp/index",
                "flow/stages/authenticator_validate/index",
                "flow/stages/authenticator_webauthn/index",
                "flow/stages/captcha/index",
                "flow/stages/deny",
                "flow/stages/email/index",
                "flow/stages/identification/index",
                "flow/stages/invitation/index",
                "flow/stages/password/index",
                "flow/stages/prompt/index",
                "flow/stages/source/index",
                "flow/stages/user_delete",
                "flow/stages/user_login/index",
                "flow/stages/user_logout",
                "flow/stages/user_write",
            ],
        },
        {
            type: "category",
            label: "Policies",
            link: {
                type: "doc",
                id: "policies/index",
            },
            items: [
                {
                    type: "category",
                    label: "Working with policies",
                    link: {
                        type: "generated-index",
                        title: "Working with policies",
                        slug: "policies/working_with_policies",
                        description: "Overview of policies configuration",
                    },
                    items: [
                        "policies/working_with_policies/whitelist_email",
                        "policies/working_with_policies/unique_email",
                    ],
                },
                "policies/expression",
            ],
        },
        {
            type: "category",
            label: "Property Mappings",
            link: {
                type: "doc",
                id: "property-mappings/index",
            },
            items: ["property-mappings/expression"],
        },
        {
            type: "category",
            label: "Events",
            link: {
                type: "doc",
                id: "events/index",
            },
            items: ["events/notifications", "events/transports"],
        },
        {
            type: "category",
            label: "Interfaces",
            items: [
                {
                    type: "category",
                    label: "Flow",
                    items: ["interfaces/flow/customization"],
                },
                {
                    type: "category",
                    label: "User",
                    items: ["interfaces/user/customization"],
                },
                {
                    type: "category",
                    label: "Admin",
                    items: ["interfaces/admin/customization"],
                },
            ],
        },
        {
            type: "category",
            label: "Users, Groups, & Roles",
            items: [
                {
                    type: "category",
                    label: "Users",
                    link: {
                        type: "doc",
                        id: "user-group-role/user/index",
                    },
                    items: [
                        "user-group-role/user/user_basic_operations",
                        "user-group-role/user/user_ref",
                        "user-group-role/user/invitations",
                    ],
                },
                {
                    type: "category",
                    label: "Groups",
                    link: {
                        type: "doc",
                        id: "user-group-role/groups/index",
                    },
                    items: ["user-group-role/groups/manage_groups"],
                },
                {
                    type: "category",
                    label: "Roles",
                    link: {
                        type: "doc",
                        id: "user-group-role/roles/index",
                    },
                    items: ["user-group-role/roles/manage_roles"],
                },
                {
                    type: "category",
                    label: "Access control",
                    link: {
                        type: "doc",
                        id: "user-group-role/access-control/index",
                    },
                    items: [
                        "user-group-role/access-control/permissions",
                        "user-group-role/access-control/manage_permissions",
                    ],
                },
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
        {
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
                    type: "category",
                    label: "PostgreSQL",
                    items: [
                        "troubleshooting/postgres/upgrade_kubernetes",
                        "troubleshooting/postgres/upgrade_docker",
                    ],
                },
                "troubleshooting/access",
                "troubleshooting/login",
                "troubleshooting/image_upload",
                "troubleshooting/missing_permission",
                "troubleshooting/missing_admin_group",
                "troubleshooting/csrf",
                "troubleshooting/emails",
                "troubleshooting/ldap_source",
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
    ],
};

docsSidebar.docs[0].value = generateVersionDropdown(docsSidebar);
module.exports = docsSidebar;
