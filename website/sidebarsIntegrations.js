const docsSidebar = require("./sidebars.js");
const generateVersionDropdown =
    require("./src/utils.js").generateVersionDropdown;

module.exports = {
    integrations: [
        {
            type: "html",
            value: generateVersionDropdown(docsSidebar),
        },
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
                    label: "Chat, Communication & Collaboration",
                    items: [
                        "services/bookstack/index",
                        "services/dokuwiki/index",
                        "services/hedgedoc/index",
                        "services/kimai/index",
                        "services/mastodon/index",
                        "services/matrix-synapse/index",
                        "services/mobilizon/index",
                        "services/nextcloud/index",
                        "services/onlyoffice/index",
                        "services/paperless-ng/index",
                        "services/rocketchat/index",
                        "services/roundcube/index",
                        "services/vikunja/index",
                        "services/wekan/index",
                        "services/wiki-js/index",
                        "services/writefreely/index",
                        "services/zulip/index",
                    ],
                },
                {
                    type: "category",
                    label: "Cloud Providers",
                    items: [
                        "services/aws/index",
                        "services/google/index",
                        "services/hashicorp-cloud/index",
                        "services/oracle-cloud/index",
                    ],
                },
                {
                    type: "category",
                    label: "Dashboards",
                    items: ["services/organizr/index"],
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
                    label: "Infrastructure",
                    items: [
                        "services/apache-guacamole/index",
                        "services/argocd/index",
                        "services/awx-tower/index",
                        "services/firezone/index",
                        "services/fortimanager/index",
                        "services/harbor/index",
                        "services/hashicorp-vault/index",
                        "services/minio/index",
                        "services/netbox/index",
                        "services/opnsense/index",
                        "services/pfsense/index",
                        "services/pgadmin/index",
                        "services/phpipam/index",
                        "services/powerdns-admin/index",
                        "services/proftpd/index",
                        "services/qnap-nas/index",
                        "services/skyhigh/index",
                        "services/snipe-it/index",
                        "services/sssd/index",
                        "services/truecommand/index",
                        "services/veeam-enterprise-manager/index",
                        "services/zammad/index",
                    ],
                },
                {
                    type: "category",
                    label: "Miscellaneous",
                    items: [
                        "services/gravitee/index",
                        "services/home-assistant/index",
                        "services/jellyfin/index",
                        "services/node-red/index",
                        "services/sonarr/index",
                        "services/tautulli/index",
                        "services/weblate/index",
                    ],
                },
                {
                    type: "category",
                    label: "Monitoring",
                    items: [
                        "services/grafana/index",
                        "services/sentry/index",
                        "services/ubuntu-landscape/index",
                        "services/uptime-kuma/index",
                        "services/zabbix/index",
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
                    label: "Version Control Systems",
                    items: [
                        "services/gitea/index",
                        "services/github-enterprise-cloud/index",
                        "services/github-enterprise-server/index",
                        "services/github-organization/index",
                        "services/gitlab/index",
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
                {
                    type: "category",
                    label: "Directory synchronization",
                    items: [
                        "sources/active-directory/index",
                        "sources/freeipa/index",
                    ],
                },
                "sources/general",
                {
                    type: "category",
                    label: "Protocols",
                    items: [
                        "sources/ldap/index",
                        "sources/oauth/index",
                        "sources/saml/index",
                    ],
                },
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
                        "sources/twitch/index",
                        "sources/plex/index",
                        "sources/twitter/index",
                    ],
                },
            ],
        },
    ],
};
