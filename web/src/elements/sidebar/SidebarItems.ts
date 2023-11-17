import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { UiThemeEnum } from "@goauthentik/api";

// The second attribute type is of string[] to help with the 'activeWhen' control, which was
// commonplace and singular enough to merit its own handler.
export type SidebarEventHandler = () => void;

export type SidebarAttributes = {
    isAbsoluteLink?: boolean | (() => boolean);
    highlight?: boolean | (() => boolean);
    expanded?: boolean | (() => boolean);
    activeWhen?: string[];
    isActive?: boolean;
};

export type SidebarEntry = {
    path: string | SidebarEventHandler | null;
    label: string;
    attributes?: SidebarAttributes | null; // eslint-disable-line
    children?: SidebarEntry[];
};

// Typescript requires the type here to correctly type the recursive path
export type SidebarRenderer = (_: SidebarEntry) => TemplateResult;

const entryKey = (entry: SidebarEntry) => `${entry.path || "no-path"}:${entry.label}`;

@customElement("ak-sidebar-items")
export class SidebarItems extends AKElement {
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

                .highlighted {
                    background-color: var(--ak-accent);
                    margin: 16px;
                }

                .highlighted .pf-c-nav__link {
                    padding-left: 0.5rem;
                }

                .pf-c-nav__link.pf-m-current::after,
                .pf-c-nav__link.pf-m-current:hover::after,
                .pf-c-nav__item.pf-m-current:not(.pf-m-expanded) .pf-c-nav__link::after {
                    --pf-c-nav__link--m-current--after--BorderColor: #fd4b2d;
                }

                .pf-c-nav__item .pf-c-nav__item::before {
                    border-bottom-width: 0;
                }

                .pf-c-nav__section + .pf-c-nav__section {
                    --pf-c-nav__section--section--MarginTop: var(--pf-global--spacer--sm);
                }
                .pf-c-nav__list .sidebar-brand {
                    max-height: 82px;
                    margin-bottom: -0.5rem;
                }
                .pf-c-nav__toggle {
                    width: calc(
                        var(--pf-c-nav__toggle--FontSize) + calc(2 * var(--pf-global--spacer--md))
                    );
                }

                nav {
                    display: flex;
                    flex-direction: column;
                    max-height: 100vh;
                    height: 100%;
                    overflow-y: hidden;
                }
                .pf-c-nav__list {
                    flex: 1 0 1fr;
                    overflow-y: auto;
                }

                .pf-c-nav__link {
                    --pf-c-nav__link--PaddingTop: 0.5rem;
                    --pf-c-nav__link--PaddingRight: 0.5rem;
                    --pf-c-nav__link--PaddingBottom: 0.5rem;
                }

                .pf-c-nav__link a {
                    flex: 1 0 max-content;
                    color: var(--pf-c-nav__link--Color);
                }

                a.pf-c-nav__link:hover {
                    color: var(--pf-c-nav__link--Color);
                    text-decoration: var(--pf-global--link--TextDecoration--hover);
                }

                .pf-c-nav__section-title {
                    font-size: 12px;
                }
                .pf-c-nav__item {
                    --pf-c-nav__item--MarginTop: 0px;
                }

                .pf-c-nav__toggle-icon {
                    padding: var(--pf-global--spacer--sm) var(--pf-global--spacer--md);
                }
            `,
        ];
    }

    @property({ type: Array })
    entries: SidebarEntry[] = [];

    @state()
    expanded: Set<string> = new Set();

    current = "";

    constructor() {
        super();
        this.renderItem = this.renderItem.bind(this);
        this.toggleExpand = this.toggleExpand.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        window.addEventListener("hashchange", this.onHashChange);
    }

    disconnectedCallback() {
        window.removeEventListener("hashchange", this.onHashChange);
        super.disconnectedCallback();
    }

    render(): TemplateResult {
        const lightThemed = { "pf-m-light": this.activeTheme === UiThemeEnum.Light };

        return html` <nav class="pf-c-nav ${classMap(lightThemed)}" aria-label="Navigation">
            <ul class="pf-c-nav__list">
                ${map(this.entries, this.renderItem)}
            </ul>
        </nav>`;
    }

    toggleExpand(entry: SidebarEntry) {
        const key = entryKey(entry);
        if (this.expanded.has(key)) {
            this.expanded.delete(key);
        } else {
            this.expanded.add(key);
        }
        this.requestUpdate();
    }

    renderItem(entry: SidebarEntry) {
        const { path, label, attributes, children } = entry;
        // Ensure the attributes are undefined, not null; they can be null in the placeholders, but
        // not when being forwarded to the correct renderer.
        const attr = attributes ?? undefined;
        const hasChildren = !!(children && children.length > 0);

        // This is grossly imperative, in that it HAS to come before the content is rendered
        // to make sure the content gets the right settings with respect to expansion.
        if (attr?.expanded) {
            this.expanded.add(entryKey(entry));
            delete attr.expanded;
        }

        const content =
            path && hasChildren
                ? this.renderLinkAndChildren(entry)
                : hasChildren
                ? this.renderLabelAndChildren(entry)
                : path
                ? this.renderLink(label, path, attr)
                : this.renderLabel(label, attr);

        const expanded = {
            "highlighted": !!attr?.highlight,
            "pf-m-expanded": this.expanded.has(entryKey(entry)),
            "pf-m-expandable": hasChildren,
        };

        return html`<li class="pf-c-nav__item ${classMap(expanded)}">${content}</li>`;
    }

    toLinkClasses(attr: SidebarAttributes) {
        return {
            "pf-m-current": !!attr.isActive,
            "pf-c-nav__link": true,
            "highlight": !!(typeof attr.highlight === "function"
                ? attr.highlight()
                : attr.highlight),
        };
    }

    renderLabel(label: string, attr: SidebarAttributes = {}) {
        return html`<div class=${classMap(this.toLinkClasses(attr))}>${label}</div>`;
    }

    // note the responsibilities pushed up to the caller
    renderLink(label: string, path: string | SidebarEventHandler, attr: SidebarAttributes = {}) {
        if (typeof path === "function") {
            return html` <a @click=${path} class=${classMap(this.toLinkClasses(attr))}>
                ${label}
            </a>`;
        }
        return html` <a
            href="${attr.isAbsoluteLink ? "" : "#"}${path}"
            class=${classMap(this.toLinkClasses(attr))}
        >
            ${label}
        </a>`;
    }

    renderChildren(children: SidebarEntry[]) {
        return html`<section class="pf-c-nav__subnav">
            <ul class="pf-c-nav__list">
                ${map(children, this.renderItem)}
            </ul>
        </section>`;
    }

    renderLabelAndChildren(entry: SidebarEntry): TemplateResult {
        const handler = () => this.toggleExpand(entry);
        return html` <div class="pf-c-nav__link">
                <div class="ak-nav__link">${entry.label}</div>
                <span class="pf-c-nav__toggle" @click=${handler}>
                    <span class="pf-c-nav__toggle-icon">
                        <i class="fas fa-angle-right" aria-hidden="true"></i>
                    </span>
                </span>
            </div>
            ${this.expanded.has(entryKey(entry))
                ? this.renderChildren(entry.children ?? [])
                : nothing}`;
    }

    renderLinkAndChildren(entry: SidebarEntry): TemplateResult {
        const handler = () => this.toggleExpand(entry);
        return html` <div class="pf-c-nav__link">
                <a
                    href="${entry.attributes?.isAbsoluteLink ? "" : "#"}${entry.path}"
                    class="ak-nav__link"
                >
                    ${entry.label}
                </a>
                <span class="pf-c-nav__toggle" @click=${handler}>
                    <span class="pf-c-nav__toggle-icon">
                        <i class="fas fa-angle-right" aria-hidden="true"></i>
                    </span>
                </span>
            </div>
            ${this.expanded.has(entryKey(entry))
                ? this.renderChildren(entry.children ?? [])
                : nothing}`;
    }
}
