import { ROUTE_SEPARATOR } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, css } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-sidebar-item")
export class SidebarItem extends AKElement {
    static get styles(): CSSResult[] {
        return [
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
    }

    @property()
    path?: string;

    activeMatchers: RegExp[] = [];

    @property({ type: Boolean })
    expanded = false;

    @property({ type: Boolean })
    isActive = false;

    @property({ type: Boolean })
    isAbsoluteLink?: boolean;

    @property({ type: Boolean })
    highlight?: boolean;

    parent?: SidebarItem;

    get childItems(): SidebarItem[] {
        const children = Array.from(this.querySelectorAll<SidebarItem>("ak-sidebar-item") || []);
        children.forEach((child) => (child.parent = this));
        return children;
    }

    @property({ attribute: false })
    set activeWhen(regexp: string[]) {
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
        this.isActive = this.matchesPath(activePath);
    }

    private matchesPath(path: string): boolean {
        if (!this.path) {
            return false;
        }
        if (this.path) {
            const ourPath = this.path.split(";")[0];
            if (new RegExp(`^${ourPath}$`).exec(path)) {
                return true;
            }
        }
        return this.activeMatchers.some((v) => {
            const match = v.exec(path);
            if (match !== null) {
                return true;
            }
            return false;
        });
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

    renderInner(): TemplateResult {
        if (this.childItems.length > 0) {
            return html`<li
                class="pf-c-nav__item ${this.expanded ? "pf-m-expandable pf-m-expanded" : ""}"
            >
                <button
                    class="pf-c-nav__link"
                    aria-expanded="true"
                    @click=${() => {
                        this.expanded = !this.expanded;
                    }}
                >
                    <slot name="label"></slot>
                    <span class="pf-c-nav__toggle">
                        <span class="pf-c-nav__toggle-icon">
                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                        </span>
                    </span>
                </button>
                <section class="pf-c-nav__subnav" ?hidden=${!this.expanded}>
                    <ul class="pf-c-nav__list">
                        <slot></slot>
                    </ul>
                </section>
            </li>`;
        }
        return html`<li class="pf-c-nav__item">
            ${this.path
                ? html`
                      <a
                          href="${this.isAbsoluteLink ? "" : "#"}${this.path}"
                          class="pf-c-nav__link ${this.isActive ? "pf-m-current" : ""}"
                      >
                          <slot name="label"></slot>
                      </a>
                  `
                : html`
                      <span class="pf-c-nav__link">
                          <slot name="label"></slot>
                      </span>
                  `}
        </li>`;
    }
}
