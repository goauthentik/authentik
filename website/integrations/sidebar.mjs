/**
 * @file Sidebar configuration for the authentik integrations.
 *
 * @import { SidebarItemCategoryConfig, SidebarItemConfig } from "@docusaurus/plugin-content-docs-types"
 */

/**
 * @satisfies {SidebarItemCategoryConfig[]}
 */
const items = [
    {
        type: "category",
        label: "Chat, Communication & Collaboration",
        items: [
            "services/espocrm/index",
            "services/hedgedoc/index",
            "services/kimai/index",
            "services/mailcow/index",
            "services/mastodon/index",
            "services/matrix-synapse/index",
            "services/mautic/index",
            "services/mobilizon/index",
            "services/nextcloud/index",
            "services/onlyoffice/index",
            "services/openproject/index",
            "services/owncloud/index",
            "services/rocketchat/index",
            "services/roundcube/index",
            "services/sharepoint-se/index",
            "services/slack/index",
            "services/thelounge/index",
            "services/vikunja/index",
            "services/wekan/index",
            "services/writefreely/index",
            "services/zulip/index",
        ],
    },
    {
        type: "category",
        label: "Device Management",
        items: ["services/apple/index", "services/fleet/index", "services/meshcentral/index"],
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
        items: ["services/organizr/index", "services/linkwarden/index", "services/homarr/index"],
    },
    {
        type: "category",
        label: "Development",
        items: [
            "services/coder/index",
            "services/engomo/index",
            "services/frappe/index",
            "services/gitea/index",
            "services/github-enterprise-cloud/index",
            "services/github-enterprise-emu/index",
            "services/github-enterprise-server/index",
            "services/github-organization/index",
            "services/gitlab/index",
            "services/gravitee/index",
            "services/jenkins/index",
            "services/node-red/index",
            "services/sonar-qube/index",
            "services/weblate/index",
        ],
    },
    {
        type: "category",
        label: "Documentation",
        items: [
            "services/bookstack/index",
            "services/dokuwiki/index",
            "services/karakeep/index",
            "services/mealie/index",
            "services/netbox/index",
            "services/outline/index",
            "services/paperless-ng/index",
            "services/paperless-ngx/index",
            "services/snipe-it/index",
            "services/tandoor/index",
            "services/wiki-js/index",
            "services/youtrack/index",
        ],
    },
    {
        type: "category",
        label: "Hypervisors / Orchestrators",
        items: [
            "services/portainer/index",
            "services/proxmox-ve/index",
            "services/rancher/index",
            "services/xen-orchestra/index",
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
            "services/harbor/index",
            "services/komodo/index",
            "services/minio/index",
            "services/omni/index",
            "services/pgadmin/index",
            "services/phpipam/index",
            "services/plesk/index",
            "services/powerdns-admin/index",
            "services/proftpd/index",
            "services/qnap-nas/index",
            "services/rustdesk-pro/index",
            "services/semaphore/index",
            "services/synology-dsm/index",
            "services/sssd/index",
            "services/terrakube/index",
            "services/truecommand/index",
            "services/veeam-enterprise-manager/index",
            "services/zammad/index",
        ],
    },
    {
        type: "category",
        label: "Networking",
        items: [
            "services/aruba-orchestrator/index",
            "services/cloudflare-access/index",
            "services/firezone/index",
            "services/fortigate-admin/index",
            "services/fortigate-ssl/index",
            "services/fortimanager/index",
            "services/gravity/index",
            "services/globalprotect/index",
            "services/netbird/index",
            "services/opnsense/index",
            "services/pangolin/index",
            "services/pfsense/index",
            "services/tailscale/index",
        ],
    },
    {
        type: "category",
        label: "Media",
        items: [
            "services/calibre-web/index",
            "services/immich/index",
            "services/freshrss/index",
            "services/jellyfin/index",
            "services/komga/index",
            "services/miniflux/index",
            "services/sonarr/index",
            "services/tautulli/index",
        ],
    },
    {
        type: "category",
        label: "Miscellaneous",
        items: [
            "services/actual-budget/index",
            "services/adventurelog/index",
            "services/filerise/index",
            "services/home-assistant/index",
            "services/open-webui/index",
            "services/zipline/index",
        ],
    },
    {
        type: "category",
        label: "Monitoring",
        items: [
            "services/beszel/index",
            "services/chronograf/index",
            "services/gatus/index",
            "services/glitchtip/index",
            "services/grafana/index",
            "services/observium/index",
            "services/sentry/index",
            "services/ubuntu-landscape/index",
            "services/uptime-kuma/index",
            "services/wazuh/index",
            "services/zabbix/index",
            "services/whats-up-docker/index",
        ],
    },
    {
        type: "category",
        label: "Platforms",
        items: [
            "services/atlassian/index",
            "services/budibase/index",
            "services/drupal/index",
            "services/pocketbase/index",
            "services/stripe/index",
            "services/wordpress/index",
        ],
    },
    {
        type: "category",
        label: "Security",
        items: [
            "services/1password/index",
            "services/bitwarden/index",
            "services/hashicorp-vault/index",
            "services/knocknoc/index",
            "services/push-security/index",
            "services/semgrep/index",
            "services/skyhigh/index",
            "services/xcreds/index",
        ],
    },
];

/**
 *
 * @param {SidebarItemConfig} item
 * @returns {string}
 */
function label(item) {
    if (typeof item === "string") return item;

    if (item.type === "html") return item.value;
    if (item.type === "autogenerated") return item.dirName;

    if (typeof item.label === "string") return item.label;
    if (typeof item.type === "string") return item.type;
    return "";
}

/**
 * @satisfies {SidebarItemConfig}
 */
const integrationsSidebar = {
    integrations: [
        {
            type: "category",
            label: "Integrations",
            collapsible: false,
            link: {
                type: "doc",
                id: "index",
            },
            items: [
                {
                    type: "doc",
                    label: "Applications",
                    id: "applications",
                },

                ...items
                    .toSorted((a, b) => label(a).localeCompare(label(b)))
                    .map((item) => {
                        if (item.type !== "category") return item;

                        return {
                            ...item,
                            link: {
                                type: "generated-index",
                            },
                        };
                    }),
            ],
        },
    ],
};

export default integrationsSidebar;
