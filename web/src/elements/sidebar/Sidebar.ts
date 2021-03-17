import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
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
        if (!this.path) {
            return html`<section class="pf-c-nav__section">
                <h2 class="pf-c-nav__section-title">${this.name}</h2>
                <ul class="pf-c-nav__list">
                    ${this._children.map((i) => until(i.render(activePath), html``))}
                </ul>
            </section>`;
        }
        return html`<li class="pf-c-nav__item ${this.hasChildren() ? "pf-m-expandable pf-m-expanded" : ""}">
            <a href="#${this.path}" class="pf-c-nav__link ${this.isActive(activePath) ? "pf-m-current" : ""}">
                ${this.name}
            </a>
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
            PFBase,
            PFPage,
            PFNav,
            AKGlobal,
            css`
                .pf-c-nav__link.pf-m-current::after,
                .pf-c-nav__link.pf-m-current:hover::after,
                .pf-c-nav__item.pf-m-current:not(.pf-m-expanded) .pf-c-nav__link::after {
                    --pf-c-nav__link--m-current--after--BorderColor: #fd4b2d;
                }

                .pf-c-nav__section + .pf-c-nav__section {
                    --pf-c-nav__section--section--MarginTop: var(--pf-global--spacer--sm);
                }
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
                .pf-c-nav__section-title {
                    font-size: 12px;
                }
                .pf-c-nav__item {
                    --pf-c-nav__item--MarginTop: 0px;
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
