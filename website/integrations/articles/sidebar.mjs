/**
 * @file Sidebar configuration for the authentik integrations.
 *
 * @import { SidebarItemCategoryConfig, SidebarItemConfig } from "@docusaurus/plugin-content-docs/src/sidebars/types.js"
 */

/**
 * @satisfies {SidebarItemCategoryConfig[]}
 */
const items = [
    {
        type: "category",
        label: "Chat, Communication & Collaboration",
        items: [
            "espocrm/index",
            "hedgedoc/index",
            "kimai/index",
            "mailcow/index",
            "mastodon/index",
            "matrix-synapse/index",
            "mautic/index",
            "mobilizon/index",
            "nextcloud/index",
            "onlyoffice/index",
            "openproject/index",
            "owncloud/index",
            "rocketchat/index",
            "roundcube/index",
            "sharepoint-se/index",
            "slack/index",
            "thelounge/index",
            "vikunja/index",
            "wekan/index",
            "writefreely/index",
            "zulip/index",
        ],
    },
    {
        type: "category",
        label: "Device Management",
        items: ["apple/index", "fleet/index", "meshcentral/index"],
    },
    {
        type: "category",
        label: "Cloud Providers",
        items: ["aws/index", "google/index", "hashicorp-cloud/index", "oracle-cloud/index"],
    },
    {
        type: "category",
        label: "Dashboards",
        items: ["organizr/index", "linkwarden/index", "homarr/index"],
    },
    {
        type: "category",
        label: "Development",
        items: [
            "coder/index",
            "engomo/index",
            "frappe/index",
            "gitea/index",
            "github-enterprise-cloud/index",
            "github-enterprise-emu/index",
            "github-enterprise-server/index",
            "github-organization/index",
            "gitlab/index",
            "gravitee/index",
            "jenkins/index",
            "node-red/index",
            "sonar-qube/index",
            "weblate/index",
        ],
    },
    {
        type: "category",
        label: "Documentation",
        items: [
            "bookstack/index",
            "dokuwiki/index",
            "karakeep/index",
            "mealie/index",
            "netbox/index",
            "outline/index",
            "paperless-ng/index",
            "paperless-ngx/index",
            "snipe-it/index",
            "tandoor/index",
            "wiki-js/index",
            "youtrack/index",
        ],
    },
    {
        type: "category",
        label: "Hypervisors / Orchestrators",
        items: [
            "portainer/index",
            "proxmox-ve/index",
            "rancher/index",
            "xen-orchestra/index",
            "vmware-vcenter/index",
        ],
    },
    {
        type: "category",
        label: "Infrastructure",
        items: [
            "apache-guacamole/index",
            "argocd/index",
            "awx-tower/index",
            "harbor/index",
            "komodo/index",
            "minio/index",
            "omni/index",
            "pgadmin/index",
            "phpipam/index",
            "plesk/index",
            "powerdns-admin/index",
            "proftpd/index",
            "qnap-nas/index",
            "rustdesk-pro/index",
            "semaphore/index",
            "synology-dsm/index",
            "sssd/index",
            "terrakube/index",
            "truecommand/index",
            "veeam-enterprise-manager/index",
            "zammad/index",
        ],
    },
    {
        type: "category",
        label: "Networking",
        items: [
            "aruba-orchestrator/index",
            "cloudflare-access/index",
            "firezone/index",
            "fortigate-admin/index",
            "fortigate-ssl/index",
            "fortimanager/index",
            "gravity/index",
            "globalprotect/index",
            "netbird/index",
            "opnsense/index",
            "pangolin/index",
            "pfsense/index",
            "tailscale/index",
        ],
    },
    {
        type: "category",
        label: "Media",
        items: [
            "calibre-web/index",
            "immich/index",
            "freshrss/index",
            "jellyfin/index",
            "komga/index",
            "miniflux/index",
            "sonarr/index",
            "tautulli/index",
        ],
    },
    {
        type: "category",
        label: "Miscellaneous",
        items: [
            "actual-budget/index",
            "adventurelog/index",
            "filerise/index",
            "home-assistant/index",
            "open-webui/index",
            "zipline/index",
        ],
    },
    {
        type: "category",
        label: "Monitoring",
        items: [
            "beszel/index",
            "chronograf/index",
            "gatus/index",
            "glitchtip/index",
            "grafana/index",
            "observium/index",
            "sentry/index",
            "ubuntu-landscape/index",
            "uptime-kuma/index",
            "wazuh/index",
            "zabbix/index",
            "whats-up-docker/index",
        ],
    },
    {
        type: "category",
        label: "Platforms",
        items: [
            "atlassian/index",
            "budibase/index",
            "drupal/index",
            "pocketbase/index",
            "stripe/index",
            "wordpress/index",
        ],
    },
    {
        type: "category",
        label: "Security",
        items: [
            "1password/index",
            "bitwarden/index",
            "hashicorp-vault/index",
            "knocknoc/index",
            "push-security/index",
            "semgrep/index",
            "skyhigh/index",
            "xcreds/index",
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
            type: "doc",
            label: "Integrations",
            id: "index",
        },
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
};

export default integrationsSidebar;
