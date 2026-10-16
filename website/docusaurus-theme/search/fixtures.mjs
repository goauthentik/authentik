/**
 * @file Records the search tests share. Two share a URL so the collapse to one hit per section is
 *   observable, one is on another site, and one is a level-5 table row.
 */

/**
 * @import { SearchRecord } from "./common.mjs";
 */

const N = null;

/**
 * @type {SearchRecord[]}
 */
export const FIXTURE_RECORDS = [
    {
        id: "proxy-top",
        site: "Documentation",
        url: "/add-secure-apps/providers/proxy/",
        anchor: "",
        hierarchy: ["Add and Secure Applications", "Proxy provider", N, N, N, N, N],
        content: "The proxy provider sits in front of an application.",
        level: 1,
        position: 0,
    },
    {
        id: "proxy-section",
        site: "Documentation",
        url: "/add-secure-apps/providers/proxy/",
        anchor: "forward-auth",
        hierarchy: ["Add and Secure Applications", "Proxy provider", "Forward auth", N, N, N, N],
        content:
            "Forward auth lets a reverse proxy ask the proxy provider whether a request is allowed.",
        level: 2,
        position: 1,
    },
    {
        id: "blueprints",
        site: "Documentation",
        url: "/customize/blueprints/",
        anchor: "",
        hierarchy: ["Customize your Instance", "Blueprints", N, N, N, N, N],
        content: "Blueprints describe objects as YAML and apply at startup.",
        level: 1,
        position: 0,
    },
    {
        id: "outposts",
        site: "Documentation",
        url: "/add-secure-apps/outposts/",
        anchor: "",
        hierarchy: ["Add and Secure Applications", "Outposts", N, N, N, N, N],
        content: "Two outposts share one service connection.",
        level: 1,
        position: 0,
    },
    {
        id: "grafana-page",
        site: "Integrations",
        url: "https://integrations.goauthentik.io/monitoring/grafana/",
        anchor: "",
        hierarchy: ["Monitoring", "Grafana", N, N, N, N, N],
        content: "Grafana is an open source analytics and monitoring solution.",
        level: 1,
        position: 0,
    },
    {
        id: "grafana-docs",
        site: "Documentation",
        url: "/install-config/grafana/",
        anchor: "",
        hierarchy: ["Installation and Configuration", "Grafana", N, N, N, N, N],
        content: "Monitor authentik with Grafana.",
        level: 1,
        position: 0,
    },
    {
        id: "row",
        site: "Documentation",
        url: "/install-config/configuration/",
        anchor: "listen",
        hierarchy: [
            "Installation and Configuration",
            "Configuration",
            "Listen",
            N,
            N,
            "Grafana",
            N,
        ],
        content: "Enabled",
        level: 5,
        position: 3,
    },
];
