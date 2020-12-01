import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import PageStyle from "@patternfly/patternfly/components/Page/page.css";
// @ts-ignore
import NavStyle from "@patternfly/patternfly/components/Nav/nav.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";

import { User } from "../../api/user";

export interface SidebarItem {
    name: string;
    path?: string[];
    children?: SidebarItem[];
    condition?: (sb: Sidebar) => boolean;
}

export const SIDEBAR_ITEMS: SidebarItem[] = [
    {
        name: "Library",
        path: ["/library/"],
    },
    {
        name: "Monitor",
        path: ["/audit/audit/"],
        condition: (sb: Sidebar): boolean => {
            return sb.user?.is_superuser || false;
        },
    },
    {
        name: "Administration",
        children: [
            {
                name: "Overview",
                path: ["/administration/overview/"],
            },
            {
                name: "System Tasks",
                path: ["/administration/tasks/"],
            },
            {
                name: "Applications",
                path: ["/administration/applications/"],
            },
            {
                name: "Sources",
                path: ["/administration/sources/"],
            },
            {
                name: "Providers",
                path: ["/administration/providers/"],
            },
            {
                name: "User Management",
                children: [
                    {
                        name: "User",
                        path: ["/administration/users/"],
                    },
                    {
                        name: "Groups",
                        path: ["/administration/groups/"],
                    },
                ],
            },
            {
                name: "Outposts",
                children: [
                    {
                        name: "Outposts",
                        path: ["/administration/outposts/"],
                    },
                    {
                        name: "Service Connections",
                        path: ["/administration/outposts/service_connections/"],
                    },
                ],
            },
            {
                name: "Policies",
                children: [
                    {
                        name: "Policies",
                        path: ["/administration/policies/"],
                    },
                    {
                        name: "Bindings",
                        path: ["/administration/policies/bindings/"],
                    },
                ],
            },
            {
                name: "Property Mappings",
                path: ["/administration/property-mappings/"],
            },
            {
                name: "Flows",
                children: [
                    {
                        name: "Flows",
                        path: ["/administration/flows/"],
                    },
                    {
                        name: "Stages",
                        path: ["/administration/stages/"],
                    },
                    {
                        name: "Prompts",
                        path: ["/administration/stages/prompts/"],
                    },
                    {
                        name: "Invitations",
                        path: ["/administration/stages/invitations/"],
                    },
                ],
            },
            {
                name: "Certificates",
                path: ["/administration/crypto/certificates/"],
            },
            {
                name: "Tokens",
                path: ["/administration/tokens/"],
            },
        ],
        condition: (sb: Sidebar): boolean => {
            return sb.user?.is_superuser || false;
        },
    },
];

@customElement("pb-sidebar")
export class Sidebar extends LitElement {
    @property()
    activePath: string;

    @property()
    user?: User;

    static get styles(): CSSResult[] {
        return [
            GlobalsStyle,
            PageStyle,
            NavStyle,
            css`
                .pf-c-nav__list .sidebar-brand {
                    max-height: 82px;
                    margin-bottom: 0.5rem;
                }
                .pf-c-nav__link {
                    --pf-c-nav__link--PaddingTop: 0.5rem;
                    --pf-c-nav__link--PaddingRight: 0.5rem;
                    --pf-c-nav__link--PaddingBottom: 0.5rem;
                }
                .pf-c-nav__subnav {
                    --pf-c-nav__subnav--PaddingBottom: 0px;
                }

                .pf-c-nav__item-bottom {
                    position: absolute;
                    bottom: 0;
                    width: 100%;
                }
            `,
        ];
    }

    constructor() {
        super();
        User.me().then((u) => (this.user = u));
        this.activePath = window.location.hash.slice(1, Infinity);
        window.addEventListener("hashchange", () => {
            this.activePath = window.location.hash.slice(1, Infinity);
        });
    }

    renderItem(item: SidebarItem): TemplateResult {
        if (item.condition) {
            const result = item.condition(this);
            if (!result) {
                return html``;
            }
        }
        return html` <li class="pf-c-nav__item ${item.children ? "pf-m-expandable pf-m-expanded" : ""}">
            ${item.path ?
        html`<a href="#${item.path}" class="pf-c-nav__link ${item.path.some((v) => v === this.activePath) ? "pf-m-current": ""}">
                        ${item.name}
                    </a>` :
        html`<a class="pf-c-nav__link" aria-expanded="true">
                        ${item.name}
                        <span class="pf-c-nav__toggle">
                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                        </span>
                    </a>
                    <section class="pf-c-nav__subnav">
                        <ul class="pf-c-nav__simple-list">
                            ${item.children?.map((i) => this.renderItem(i))}
                        </ul>
                    </section>`}
        </li>`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-page__sidebar-body">
            <nav class="pf-c-nav" aria-label="Global">
                <ul class="pf-c-nav__list">
                    <li class="pf-c-nav__item sidebar-brand">
                        <pb-sidebar-brand></pb-sidebar-brand>
                    </li>
                    ${SIDEBAR_ITEMS.map((i) => this.renderItem(i))}
                    <li class="pf-c-nav__item pf-c-nav__item-bottom">
                        <pb-sidebar-user .user=${this.user}></pb-sidebar-user>
                    </li>
                </ul>
            </nav>
        </div>`;
    }
}
