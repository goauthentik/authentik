import {
    css,
    customElement,
    html,
    LitElement,
    property,
    TemplateResult,
} from "lit-element";
// @ts-ignore
import PageStyle from "@patternfly/patternfly/components/Page/page.css";
// @ts-ignore
import NavStyle from "@patternfly/patternfly/components/Nav/nav.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";
import { User } from "../api/user";

export interface SidebarItem {
    name: string;
    path?: string;
    children?: SidebarItem[];
    condition?: (sb: SideBar) => boolean;
}

export const SIDEBAR_ITEMS: SidebarItem[] = [
    {
        name: "General",
        children: [
            {
                name: "Overview",
                path: "administration/overview",
            },
            {
                name: "System Tasks",
                path: "administration/tasks",
            },
        ],
    },
    {
        name: "Applications",
        path: "administration/applications",
    },
    {
        name: "Sources",
        path: "administration/sources",
    },
    {
        name: "Providers",
        path: "administration/providers",
    },
    {
        name: "User Management",
        children: [
            {
                name: "User",
                path: "administration/users",
            },
            {
                name: "Groups",
                path: "administration/groups",
            },
        ],
    },
    {
        name: "Outposts",
        children: [
            {
                name: "Outposts",
                path: "administration/outposts",
            },
            {
                name: "Service Connections",
                path: "administration/outposts/service_connections",
            },
        ],
    },
    {
        name: "Policies",
        path: "administration/policies",
    },
    {
        name: "Property Mappings",
        path: "administration/property_mappings",
    },
    {
        name: "Flows",
        children: [
            {
                name: "Flows",
                path: "administration/flows",
            },
            {
                name: "Stages",
                path: "administration/stages",
            },
            {
                name: "Prompts",
                path: "administration/stages/prompts",
            },
            {
                name: "Invitations",
                path: "administration/stages/invitations",
            },
        ],
    },
    {
        name: "Certificates",
        path: "administration/crypto/certificates",
    },
    {
        name: "Tokens",
        path: "administration/tokens",
    },
];

export const ROOT_ITEMS: SidebarItem[] = [
    {
        name: "Library",
        path: "/-/overview/",
    },
    {
        name: "Monitor",
        path: "/audit/audit/",
        condition: (sb: SideBar) => {
            return sb.user?.is_superuser!;
        },
    },
    {
        name: "Administration",
        children: SIDEBAR_ITEMS,
        condition: (sb: SideBar) => {
            return sb.user?.is_superuser!;
        },
    },
];

@customElement("pb-sidebar")
export class SideBar extends LitElement {
    @property()
    activePath: string;

    @property()
    brandLogo?: string;

    @property()
    brandTitle?: string;

    @property()
    user?: User;

    static get styles() {
        return [
            GlobalsStyle,
            PageStyle,
            NavStyle,
            css`
                .pf-c-nav__link {
                    --pf-c-nav__link--PaddingTop: 0.5rem;
                    --pf-c-nav__link--PaddingRight: 0.5rem;
                    --pf-c-nav__link--PaddingBottom: 0.5rem;
                }
                .pf-c-nav__subnav {
                    --pf-c-nav__subnav--PaddingBottom: 0px;
                }
                .pb-brand {
                    font-family: "DIN 1451 Std";
                    line-height: 60px;
                    display: flex;
                    font-size: 3rem;
                    flex-direction: row;
                    align-items: center;
                    margin-right: 0.5em;
                    color: var(--pf-c-nav__link--m-current--Color);
                    text-align: center;
                }
                .pb-brand img {
                    margin: 0 0.5rem;
                    max-height: 60px;
                }
            `,
        ];
    }

    constructor() {
        super();
        fetch("/api/v2beta/core/users/me/")
            .then((r) => r.json())
            .then((r) => (this.user = <User>r));
        this.activePath = window.location.hash.slice(1, Infinity);
        window.addEventListener("hashchange", (e) => {
            this.activePath = window.location.hash.slice(1, Infinity);
        });
    }

    renderBrand(): TemplateResult {
        return html`<li class="pf-c-nav__item">
            <a href="#/" class="pf-c-page__header-brand-link">
                <div class="pf-c-brand pb-brand">
                    <img src="${this.brandLogo}" alt="passbook icon" />
                    ${this.brandTitle
                        ? html`<span>${this.brandTitle}</span>`
                        : ""}
                </div>
            </a>
        </li>`;
    }

    renderItem(item: SidebarItem): TemplateResult {
        if (item.condition) {
            const result = item.condition(this);
            if (!result) {
                return html``;
            }
        }
        return html` <li
            class="pf-c-nav__item ${item.children
                ? "pf-m-expandable pf-m-expanded"
                : ""}"
        >
            ${item.path
                ? html`<a
                      href="#${item.path}"
                      class="pf-c-nav__link ${item.path === this.activePath
                          ? "pf-m-current"
                          : ""}"
                  >
                      ${item.name}
                  </a>`
                : html`<a class="pf-c-nav__link" aria-expanded="true"
                          >${item.name}
                          <span class="pf-c-nav__toggle">
                              <i
                                  class="fas fa-angle-right"
                                  aria-hidden="true"
                              ></i>
                          </span>
                      </a>
                      <section class="pf-c-nav__subnav">
                          <ul class="pf-c-nav__simple-list">
                              ${item.children?.map((i) => this.renderItem(i))}
                          </ul>
                      </section>`}
        </li>`;
    }

    render() {
        return html`<div class="pf-c-page__sidebar-body">
            <nav class="pf-c-nav" aria-label="Global">
                <ul class="pf-c-nav__list">
                    ${this.renderBrand()}
                    ${ROOT_ITEMS.map((i) => this.renderItem(i))}
                </ul>
            </nav>
        </div>`;
    }
}
