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
            label: "Installation and Configuration ",
            collapsed: true,
            link: {
                type: "doc",
                id: "install-config/index",
            },
            items: [
                "install-config/install/docker-compose",
                "install-config/install/kubernetes",
                "install-config/configuration/configuration",
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
            label: "Core Concepts",
            collapsed: true,
            items: [
                "core/terminology",
                "core/architecture",
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

                    type: "category",
                    label: "Roles",
                    link: {
                        type: "doc",
                        id: "user-sources/roles/index",
                    },
                    items: [
                        "user-sources/groups/manage_roles",
                    ],

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

                    type: "category",
                    label: "Federated and Social Sources",
                    collapsed: true,
                    link: {
                        type: "doc",
                        id: "user-sources/index",
                    },
                    items: [
                        {
                        type: "category",
                        label: "Protocols",
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
                            items: ["user-sources/sources/property-mappings/expressions"],
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
        {
            type: "category",
            label: "Customize your authentik Instance",
            collapsed: true,
            link: {
                type: "doc",
                id: "customize/index",
            },
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
                        id: "customize/policies/working_with_policies/working_with_policies.md",
                    },
                    items: [
                        "customize/policies/working_with_policies/unique_email.md",
                        "customize/policies/working_with_policies/whitelist_email.md",
                    ],
                },
            ],
        };

    docsSidebar.docs[0].value = generateVersionDropdown(docsSidebar);
    module.exports = docsSidebar;
