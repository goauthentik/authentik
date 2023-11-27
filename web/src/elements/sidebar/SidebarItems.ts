import { ROUTE_SEPARATOR } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import { findTable } from "@goauthentik/elements/table/TablePage";

import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { UiThemeEnum } from "@goauthentik/api";

import type { SidebarEntry } from "./types";
import { entryKey, findMatchForNavbarUrl, makeParentMap } from "./utils";

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
        this.onHashChange = this.onHashChange.bind(this);
        this.reclick = this.reclick.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        window.addEventListener("hashchange", this.onHashChange);
    }

    disconnectedCallback() {
        window.removeEventListener("hashchange", this.onHashChange);
        super.disconnectedCallback();
    }

    expandParents(entry: SidebarEntry) {
        const reverseMap = makeParentMap(this.entries);
        let start: SidebarEntry | undefined = reverseMap.get(entry);
        while (start) {
            this.expanded.add(entryKey(start));
            start = reverseMap.get(start);
        }
    }

    onHashChange() {
        this.current = "";
        const match = findMatchForNavbarUrl(this.entries);
        if (match) {
            this.current = entryKey(match);
            this.expandParents(match);
        }
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

    // This is gross and feels like 2007: using a path from the root through the shadowDoms (see
    // `TablePage:findTable()`), this code finds the element that *should* be triggered by an event
    // on the URL, and forcibly injects the text of the search and the click of the search button.

    reclick(ev: Event, path: string) {
        const oldPath = window.location.hash.split(ROUTE_SEPARATOR)[0];
        const [curPath, ...curSearchComponents] = path.split(ROUTE_SEPARATOR);
        const curSearch: string =
            curSearchComponents.length > 0 ? curSearchComponents.join(ROUTE_SEPARATOR) : "";

        if (curPath !== oldPath) {
            // A Tier 1 or Tier 2 change should be handled by the router. (So should a Tier 3
            // change, but... here we are.)
            return;
        }

        const table = findTable();
        if (!table) {
            return;
        }

        // Always wrap the minimal exceptional code possible in an IIFE and supply the failure
        // alternative. Turn exceptions into expressions with the smallest functional rewind
        // whenever possible.
        const search = (() => {
            try {
                return curSearch ? JSON.parse(decodeURIComponent(curSearch)) : { search: "" };
            } catch {
                return { search: "" };
            }
        })();

        if ("search" in search) {
            ev.preventDefault();
            ev.stopPropagation();
            table.search = search.search;
            table.fetch();
        }
    }

    render(): TemplateResult {
        const lightThemed = { "pf-m-light": this.activeTheme === UiThemeEnum.Light };

        return html` <nav class="pf-c-nav ${classMap(lightThemed)}" aria-label="Navigation">
            <ul class="pf-c-nav__list">
                ${map(this.entries, this.renderItem)}
            </ul>
        </nav>`;
    }

    renderItem(entry: SidebarEntry) {
        // Ensure the attributes are undefined, not null; they can be null in the placeholders, but
        // not when being forwarded to the correct renderer.
        const hasChildren = !!(entry.children && entry.children.length > 0);

        // This is grossly imperative, in that it HAS to come before the content is rendered to make
        // sure the content gets the right settings with respect to expansion.
        if (entry.attributes?.expanded) {
            this.expanded.add(entryKey(entry));
            delete entry.attributes.expanded;
        }

        const content =
            entry.path && hasChildren
                ? this.renderLinkAndChildren(entry)
                : hasChildren
                  ? this.renderLabelAndChildren(entry)
                  : entry.path
                    ? this.renderLink(entry)
                    : this.renderLabel(entry);

        const expanded = {
            "highlighted": !!entry.attributes?.highlight,
            "pf-m-expanded": this.expanded.has(entryKey(entry)),
            "pf-m-expandable": hasChildren,
        };

        return html`<li class="pf-c-nav__item ${classMap(expanded)}">${content}</li>`;
    }

    getLinkClasses(entry: SidebarEntry) {
        const a = entry.attributes ?? {};
        return {
            "pf-m-current": a == this.current,
            "pf-c-nav__link": true,
            "highlight": !!(typeof a.highlight === "function" ? a.highlight() : a.highlight),
        };
    }

    renderLabel(entry: SidebarEntry) {
        return html`<div class=${classMap(this.getLinkClasses(entry))}>${entry.label}</div>`;
    }

    // note the responsibilities pushed up to the caller
    renderLink(entry: SidebarEntry) {
        if (typeof entry.path === "function") {
            return html` <a @click=${entry.path} class=${classMap(this.getLinkClasses(entry))}>
                ${entry.label}
            </a>`;
        }
        const path = `${entry.attributes?.isAbsoluteLink ? "" : "#"}${entry.path}`;
        return html` <a
            href=${path}
            @click=${(ev: Event) => this.reclick(ev, path)}
            class=${classMap(this.getLinkClasses(entry))}
        >
            ${entry.label}
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
        const path = `${entry.attributes?.isAbsoluteLink ? "" : "#"}${entry.path}`;
        return html` <div class="pf-c-nav__link">
                <a
                    href=${path}
                    @click=${(ev: Event) => this.reclick(ev, path)}
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
