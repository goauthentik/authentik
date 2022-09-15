module.exports = {
    integrations: [
        {
            type: "category",
            label: "Applications",
            link: {
                type: "doc",
                id: "services/index",
            },
            items: [
                {
                    type: "category",
                    label: "Infrastructure",
                    items: [
                        "services/apache-guacamole/index",
                        "services/awx-tower/index",
                        "services/fortimanager/index",
                        "services/harbor/index",
                        "services/hashicorp-vault/index",
                        "services/minio/index",
                        "services/opnsense/index",
                        "services/pfsense/index",
                        "services/pgadmin/index",
                        "services/powerdns-admin/index",
                        "services/veeam-enterprise-manager/index",
                    ],
                },
                {
                    type: "category",
                    label: "Hypervisors / Orchestrators",
                    items: [
                        "services/portainer/index",
                        "services/proxmox-ve/index",
                        "services/rancher/index",
                        "services/vmware-vcenter/index",
                    ],
                },
                {
                    type: "category",
                    label: "Monitoring",
                    items: [
                        "services/grafana/index",
                        "services/ubuntu-landscape/index",
                        "services/uptime-kuma/index",
                        "services/zabbix/index",
                    ],
                },
                {
                    type: "category",
                    label: "Cloud Providers",
                    items: [
                        "services/aws/index",
                        "services/oracle-cloud/index",
                    ],
                },
                {
                    type: "category",
                    label: "Chat, Communication & Collaboration",
                    items: [
                        "services/bookstack/index",
                        "services/hedgedoc/index",
                        "services/kimai/index",
                        "services/matrix-synapse/index",
                        "services/nextcloud/index",
                        "services/onlyoffice/index",
                        "services/paperless-ng/index",
                        "services/rocketchat/index",
                        "services/roundcube/index",
                        "services/vikunja/index",
                        "services/wekan/index",
                        "services/wiki-js/index",
                        "services/zulip/index",
                    ],
                },
                {
                    type: "category",
                    label: "Platforms",
                    items: [
                        "services/budibase/index",
                        "services/wordpress/index",
                    ],
                },
                {
                    type: "category",
                    label: "Developer tools",
                    items: [
                        "services/sentry/index",
                        "services/sssd/index",
                        "services/weblate/index",
                    ],
                },
                {
                    type: "category",
                    label: "Version Control Systems",
                    items: [
                        "services/gitea/index",
                        "services/github-enterprise-cloud/index",
                        "services/github-organization/index",
                        "services/gitlab/index",
                    ],
                },
                {
                    type: "category",
                    label: "Miscellaneous",
                    items: [
                        "services/home-assistant/index",
                        "services/node-red/index",
                        "services/sonarr/index",
                        "services/tautulli/index",
                    ],
                },
            ],
        },
        {
            type: "category",
            label: "Federation & Social login",
            link: {
                type: "generated-index",
                title: "Sources",
                slug: "sources",
                description:
                    "Sources of users which can be federated with authentik",
            },
            items: [
                "sources/general",
                {
                    type: "category",
                    label: "Social Logins",
                    items: [
                        "sources/apple/index",
                        "sources/azure-ad/index",
                        "sources/discord/index",
                        "sources/github/index",
                        "sources/google/index",
                        "sources/mailcow/index",
                        "sources/plex/index",
                        "sources/twitter/index",
                    ],
                },
                {
                    type: "category",
                    label: "Directory syncronization",
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
                    ],
                },
            ],
        },
    ],
};
