module.exports = {
    docs: [
        {
            type: "doc",
            id: "index",
        },
        {
            type: "category",
            label: "Installation",
            collapsed: false,
            link: {
                type: "generated-index",
                title: "Installation",
                slug: "installation",
                description:
                    "Everything you need to get authentik up and running!",
            },
            items: [
                "installation/docker-compose",
                "installation/kubernetes",
                "installation/beta",
                "installation/configuration",
                "installation/reverse-proxy",
                "installation/automated-install",
                "installation/air-gapped",
            ],
        },
        {
            type: "category",
            label: "Core Concepts",
            collapsed: false,
            items: [
                "core/terminology",
                "core/applications",
                "core/tenants",
                "core/certificates",
            ],
        },
        {
            type: "category",
            label: "Providers",
            items: [
                {
                    type: "category",
                    label: "OAuth2 Provider",
                    link: {
                        type: "doc",
                        id: "providers/oauth2/index",
                    },
                    items: ["providers/oauth2/client_credentials"],
                },
                "providers/saml",
                {
                    type: "category",
                    label: "Proxy Provider",
                    link: {
                        type: "doc",
                        id: "providers/proxy/index",
                    },
                    items: [
                        "providers/proxy/custom_headers",
                        "providers/proxy/forward_auth",
                    ],
                },
                "providers/ldap",
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
                "flow/stages/user_delete",
                "flow/stages/user_login",
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
            items: ["policies/expression"],
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
            label: "Users & Groups",
            items: ["user-group/user", "user-group/group"],
        },
        {
            type: "category",
            label: "Release Notes",
            link: {
                type: "generated-index",
                title: "Releases",
                slug: "releases",
                description: "Release notes for recent authentik versions",
            },
            items: [
                "releases/v2022.9",
                "releases/v2022.8",
                "releases/v2022.7",
                {
                    type: "category",
                    label: "Previous versions",
                    items: [
                        "releases/v2022.6",
                        "releases/v2022.5",
                        "releases/v2022.4",
                        "releases/v2022.2",
                        "releases/v2022.1",
                        "releases/v2021.12",
                        "releases/v2021.10",
                        "releases/v2021.9",
                        "releases/v2021.8",
                        "releases/v2021.7",
                        "releases/v2021.6",
                        "releases/v2021.5",
                        "releases/v2021.4",
                        "releases/v2021.3",
                        "releases/v2021.2",
                        "releases/v2021.1",
                        "releases/v0.14",
                        "releases/v0.13",
                        "releases/v0.12",
                        "releases/v0.11",
                        "releases/v0.10",
                        "releases/v0.9",
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
                "troubleshooting/access",
                "troubleshooting/emails",
                "troubleshooting/login",
                "troubleshooting/image_upload",
                "troubleshooting/missing_permission",
                "troubleshooting/missing_admin_group",
            ],
        },
    ],
};
