import { ROUTE_SEPARATOR } from "#common/constants";

import { AKElement } from "#elements/Base";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface SidebarItemProperties {
    path?: string;
    activeWhen?: string[];
    expanded?: boolean;
}

@customElement("ak-sidebar-item")
export class SidebarItem extends AKElement {
    static styles: CSSResult[] = [
        PFBase,
        PFPage,
        PFNav,
        css`
            :host {
                z-index: 100;
                box-shadow: none !important;
            }
            :host([highlight]) .pf-c-nav__item {
                background-color: var(--ak-accent);
                margin: 16px;
            }
            :host([highlight]) .pf-c-nav__item .pf-c-nav__link {
                padding-left: 0.5rem;
            }
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

    @property()
    public path?: string;

    @property({ type: String })
    public label?: string;

    activeMatchers: RegExp[] = [];

    @property({ type: Boolean })
    public expanded = false;

    @property({ type: Boolean })
    public current?: boolean;

    @property({ type: Boolean })
    public isAbsoluteLink = false;

    @property({ type: Boolean })
    public highlight?: boolean;

    public parent?: SidebarItem;

    public get childItems(): SidebarItem[] {
        const children = Array.from(this.querySelectorAll<SidebarItem>("ak-sidebar-item") || []);
        children.forEach((child) => (child.parent = this));
        return children;
    }

    @property({ attribute: false })
    public set activeWhen(regexp: string[]) {
        regexp.forEach((r) => {
            this.activeMatchers.push(new RegExp(r));
        });
    }

    firstUpdated(): void {
        this.onHashChange();
        window.addEventListener("hashchange", () => this.onHashChange());
    }

    onHashChange(): void {
        const activePath = window.location.hash.slice(1, Infinity).split(ROUTE_SEPARATOR)[0];
        this.childItems.forEach((item) => {
            this.expandParentRecursive(activePath, item);
        });
        this.current = this.matchesPath(activePath);
    }

    private matchesPath(path: string): boolean {
        if (!this.path) {
            return false;
        }

        const ourPath = this.path.split(";")[0];
        const pathIsWholePath = new RegExp(`^${ourPath}$`).test(path);
        const pathIsAnActivePath = this.activeMatchers.some((v) => v.test(path));
        return pathIsWholePath || pathIsAnActivePath;
    }

    expandParentRecursive(activePath: string, item: SidebarItem): void {
        if (item.matchesPath(activePath) && item.parent) {
            item.parent.expanded = true;
            this.requestUpdate();
        }
        item.childItems.forEach((i) => this.expandParentRecursive(activePath, i));
    }

    render(): TemplateResult {
        return this.renderInner();
    }

    renderWithChildren() {
        return html`<li
            aria-label=${ifDefined(this.label)}
            role="heading"
            class="pf-c-nav__item ${this.expanded ? "pf-m-expandable pf-m-expanded" : ""}"
        >
            <button
                class="pf-c-nav__link"
                aria-label=${this.expanded
                    ? msg(str`Collapse ${this.label}`)
                    : msg(str`Expand ${this.label}`)}
                aria-expanded=${this.expanded ? "true" : "false"}
                aria-controls="subnav-${this.path}"
                @click=${() => {
                    this.expanded = !this.expanded;
                }}
            >
                ${this.label}
                <span class="pf-c-nav__toggle">
                    <span class="pf-c-nav__toggle-icon">
                        <i class="fas fa-angle-right" aria-hidden="true"></i>
                    </span>
                </span>
            </button>
            <div class="pf-c-nav__subnav" ?hidden=${!this.expanded}>
                <ul
                    id="subnav-${this.path}"
                    role="navigation"
                    aria-label=${msg(str`${this.label} navigation`)}
                    class="pf-c-nav__list"
                    ?hidden=${!this.expanded}
                >
                    ${this.expanded ? html`<slot></slot>` : nothing}
                </ul>
            </div>
        </li>`;
    }

    renderWithPathAndChildren() {
        return html`<li
            role="presentation"
            aria-label=${ifDefined(this.label)}
            class="pf-c-nav__item ${this.expanded ? "pf-m-expandable pf-m-expanded" : ""}"
        >
            ${this.label}
            <button
                aria-label=${this.expanded
                    ? msg(str`Collapse ${this.label}`)
                    : msg(str`Expand ${this.label}`)}
                class="pf-c-nav__link"
                aria-expanded="true"
                @click=${() => {
                    this.expanded = !this.expanded;
                }}
            >
                <span class="pf-c-nav__toggle">
                    <span class="pf-c-nav__toggle-icon">
                        <i class="fas fa-angle-right" aria-hidden="true"></i>
                    </span>
                </span>
            </button>
            <div class="pf-c-nav__subnav" ?hidden=${!this.expanded}>
                <ul class="pf-c-nav__list">
                    <slot></slot>
                </ul>
            </div>
        </li>`;
    }

    renderWithPath() {
        return html`
            <a
                id="sidebar-nav-link-${this.path}"
                href="${this.isAbsoluteLink ? "" : "#"}${this.path}"
                class="pf-c-nav__link ${this.current ? "pf-m-current" : ""}"
                aria-current=${ifDefined(this.current ? "page" : undefined)}
            >
                ${this.label}
            </a>
        `;
    }

    renderWithLabel() {
        return html` <span class="pf-c-nav__link"> ${this.label} </span> `;
    }

    renderInner() {
        if (this.childItems.length > 0) {
            return this.path ? this.renderWithPathAndChildren() : this.renderWithChildren();
        }

        return html`<li
            role="presentation"
            aria-label=${ifDefined(this.label)}
            class="pf-c-nav__item"
        >
            ${this.path ? this.renderWithPath() : this.renderWithLabel()}
        </li>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar-item": SidebarItem;
    }
}
