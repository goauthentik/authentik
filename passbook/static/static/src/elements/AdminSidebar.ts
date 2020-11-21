import {
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

export interface SidebarItem {
    name: string;
    path?: string;
    children?: SidebarItem[];
}

export const SIDEBAR_ITEMS: SidebarItem[] = [
    {
        name: "Overview",
        path: "overview",
    },
    {
        name: "Applications",
        path: "applications",
    },
    {
        name: "Sources",
        path: "sources",
    },
    {
        name: "Providers",
        path: "providers",
    },
    {
        name: "Outposts",
        children: [
            {
                name: "Outposts",
                path: "outposts",
            },
            {
                name: "Service Connections",
                path: "outposts/service_connections",
            },
        ],
    },
    {
        name: "Property Mappings",
        path: "property_mappings",
    },
    {
        name: "Flows",
        children: [
            {
                name: "Flows",
                path: "flows",
            },
            {
                name: "Bindings",
                path: "stages/bindings",
            },
            {
                name: "Stages",
                path: "stages",
            },
            {
                name: "Prompts",
                path: "stages/prompts",
            },
            {
                name: "Invitations",
                path: "stages/invitations",
            },
        ],
    },
    {
        name: "Policies",
        children: [
            {
                name: "Policies",
                path: "policies",
            },
            {
                name: "Bindings",
                path: "policies/bindings",
            },
        ],
    },
    {
        name: "Certificates",
        path: "crypto/certificates",
    },
    {
        name: "Tokens",
        path: "tokens",
    },
    {
        name: "User",
        path: "users",
    },
    {
        name: "Groups",
        path: "groups",
    },
    {
        name: "System Tasks",
        path: "tasks",
    },
];

@customElement("pb-admin-sidebar")
export class AdminSideBar extends LitElement {
    @property()
    activePath: string;

    static get styles() {
        return [GlobalsStyle, PageStyle, NavStyle];
    }

    constructor() {
        super();
        this.activePath = window.location.hash.slice(1, Infinity);
        window.addEventListener("hashchange", (e) => {
            this.activePath = window.location.hash.slice(1, Infinity);
        });
    }

    renderItem(item: SidebarItem): TemplateResult {
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
                    ${SIDEBAR_ITEMS.map((i) => this.renderItem(i))}
                </ul>
            </nav>
        </div>`;
    }
}
