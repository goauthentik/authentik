import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import PageStyle from "@patternfly/patternfly/components/Page/page.css";
// @ts-ignore
import NavStyle from "@patternfly/patternfly/components/Nav/nav.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";
// @ts-ignore
import AKGlobal from "../../authentik.css";

import { until } from "lit-html/directives/until";

import "./SidebarBrand";
import "./SidebarUser";

export class SidebarItem {
    name: string;
    path?: string;

    _children: SidebarItem[];
    condition: () => Promise<boolean>;

    activeMatchers: RegExp[];

    constructor(name: string, path?: string) {
        this.name = name;
        this.path = path;
        this._children = [];
        this.condition = async () => true;
        this.activeMatchers = [];
        if (this.path) {
            this.activeMatchers.push(new RegExp(`^${this.path}$`));
        }
    }

    children(...children: SidebarItem[]): SidebarItem {
        this._children = children;
        return this;
    }

    activeWhen(...regexp: string[]): SidebarItem {
        regexp.forEach(r => {
            this.activeMatchers.push(new RegExp(r));
        });
        return this;
    }

    when(condition: () => Promise<boolean>): SidebarItem {
        this.condition = condition;
        return this;
    }

    hasChildren(): boolean {
        return this._children.length > 0;
    }

    isActive(activePath: string): boolean {
        if (!this.path) {
            return false;
        }
        return this.activeMatchers.some(v => {
            const match = v.exec(activePath);
            if (match !== null) {
                return true;
            }
        });
    }

    async render(activePath: string): Promise<TemplateResult> {
        if (this.condition) {
            const result = await this.condition();
            if (!result) {
                return html``;
            }
        }
        return html` <li class="pf-c-nav__item ${this.hasChildren() ? "pf-m-expandable pf-m-expanded" : ""}">
            ${this.path ?
                html`<a href="#${this.path}" class="pf-c-nav__link ${this.isActive(activePath) ? "pf-m-current" : ""}">
                        ${this.name}
                    </a>` :
                html`<a class="pf-c-nav__link" aria-expanded="true">
                        ${this.name}
                        <span class="pf-c-nav__toggle">
                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                        </span>
                    </a>
                    <section class="pf-c-nav__subnav">
                        <ul class="pf-c-nav__simple-list">
                            ${this._children.map((i) => until(i.render(activePath), html``))}
                        </ul>
                    </section>`}
        </li>`;
    }
}

@customElement("ak-sidebar")
export class Sidebar extends LitElement {
    @property({attribute: false})
    items: SidebarItem[] = [];

    @property()
    activePath: string;

    static get styles(): CSSResult[] {
        return [
            GlobalsStyle,
            PageStyle,
            NavStyle,
            AKGlobal,
            css`
                .pf-c-nav__list .sidebar-brand {
                    max-height: 82px;
                    margin-bottom: -0.5rem;
                }
                nav {
                    display: flex;
                    flex-direction: column;
                    max-height: 100vh;
                    height: 100%;
                    overflow-y: hidden;
                }
                .pf-c-nav__list {
                    flex-grow: 1;
                    overflow-y: auto;
                }

                .pf-c-nav__link {
                    --pf-c-nav__link--PaddingTop: 0.5rem;
                    --pf-c-nav__link--PaddingRight: 0.5rem;
                    --pf-c-nav__link--PaddingBottom: 0.5rem;
                }
                .pf-c-nav__subnav {
                    --pf-c-nav__subnav--PaddingBottom: 0px;
                }
            `,
        ];
    }

    constructor() {
        super();
        this.activePath = window.location.hash.slice(1, Infinity);
        window.addEventListener("hashchange", () => {
            this.activePath = window.location.hash.slice(1, Infinity);
        });
    }

    render(): TemplateResult {
        return html`<nav class="pf-c-nav" aria-label="Global">
            <ak-sidebar-brand></ak-sidebar-brand>
            <ul class="pf-c-nav__list">
                ${this.items.map((i) => until(i.render(this.activePath), html``))}
            </ul>
            <ak-sidebar-user></ak-sidebar-user>
        </nav>`;
    }
}
