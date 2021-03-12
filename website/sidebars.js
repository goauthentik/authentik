module.exports = {
    docs: [
        {
            type: "doc",
            id: "index",
        },
        {
            type: "doc",
            id: "terminology",
        },
        {
            type: "category",
            label: "Installation",
            items: [
                "installation/index",
                "installation/docker-compose",
                "installation/docker-compose-config",
                "installation/reverse-proxy",
                "installation/kubernetes",
                "installation/beta",
            ],
        },
        {
            type: "doc",
            id: "sources",
        },
        {
            type: "category",
            label: "Providers",
            items: ["providers/oauth2", "providers/saml", "providers/proxy"],
        },
        {
            type: "category",
            label: "Outposts",
            items: [
                "outposts/outposts",
                "outposts/upgrading",
                "outposts/manual-deploy-docker-compose",
                "outposts/manual-deploy-kubernetes",
            ],
        },
        {
            type: "category",
            label: "Flows",
            items: ["flow/flows", "flow/examples"],
        },
        {
            type: "category",
            label: "Stages",
            items: [
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
                "flow/stages/prompt/validation",
                "flow/stages/user_delete",
                "flow/stages/user_login",
                "flow/stages/user_logout",
                "flow/stages/user_write",
            ],
        },
        {
            type: "category",
            label: "Policies",
            items: ["policies/index", "policies/expression"],
        },
        {
            type: "category",
            label: "Property Mappings",
            items: ["property-mappings/index", "property-mappings/expression"],
        },
        {
            type: "category",
            label: "Expressions",
            items: [
                "expressions/index",
                {
                    type: "category",
                    label: "Reference",
                    items: ["expressions/reference/user-object"],
                },
            ],
        },
        {
            type: "category",
            label: "Events",
            items: [
                "events/index",
                "events/notifications",
                "events/transports"
            ],
        },
        {
            type: "category",
            label: "Integrations",
            items: [
                {
                    type: "category",
                    label: "as Source",
                    items: ["integrations/sources/active-directory/index"],
                },
                {
                    type: "category",
                    label: "as Provider",
                    items: [
                        "integrations/services/apache-guacamole/index",
                        "integrations/services/aws/index",
                        "integrations/services/awx-tower/index",
                        "integrations/services/gitlab/index",
                        "integrations/services/grafana/index",
                        "integrations/services/harbor/index",
                        "integrations/services/home-assistant/index",
                        "integrations/services/nextcloud/index",
                        "integrations/services/rancher/index",
                        "integrations/services/sentry/index",
                        "integrations/services/sonarr/index",
                        "integrations/services/tautulli/index",
                        "integrations/services/ubuntu-landscape/index",
                        "integrations/services/veeam-enterprise-manager/index",
                        "integrations/services/vmware-vcenter/index",
                        "integrations/services/wiki-js/index",
                    ],
                },
            ],
        },
        {
            type: "category",
            label: "Maintenance",
            items: ["maintenance/backups/index"],
        },
        {
            type: "category",
            label: "Release Notes",
            items: [
                "releases/0.9",
                "releases/0.10",
                "releases/0.11",
                "releases/0.12",
                "releases/0.13",
                "releases/0.14",
                "releases/2021.1",
                "releases/2021.2",
                "releases/2021.3",
            ],
        },
        {
            type: "category",
            label: "Troubleshooting",
            items: [
                "troubleshooting/access",
                "troubleshooting/emails",
                "troubleshooting/login",
            ],
        },
        {
            type: "category",
            label: "Development",
            items: ["development/local-dev-environment"],
        },
    ],
};
