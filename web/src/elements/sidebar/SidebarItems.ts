import { ROUTE_SEPARATOR } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import { findTable } from "@goauthentik/elements/table/TablePage";

import { TemplateResult, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { map } from "lit/directives/map.js";

import { UiThemeEnum } from "@goauthentik/api";

import { sidebarItemStyles } from "./SidebarItems.css.js";
import type { SidebarEntry } from "./types";
import { entryKey, findMatchForNavbarUrl, makeParentMap } from "./utils";

/**
 * Display the sidebar item tree.
 *
 * Along with the `reclick()` complaint down below, the other thing I dislike about this design is
 * that it's effectively two different programs glued together. The first responds to the `click`
 * and performs the navigation, which either triggers the router or triggers a new search on the
 * existing view. The second responds to the navigation change event when the URL is changed by the
 * navigation event, at which point it figures out which entry to highlight as "current," which
 * causes the re-render.
 */

@customElement("ak-sidebar-items")
export class SidebarItems extends AKElement {
    static get styles() {
        return sidebarItemStyles;
    }

    @property({ type: Array })
    entries: SidebarEntry[] = [];

    expanded: Set<string> = new Set();

    @state()
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
        this.onHashChange();
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
        console.log("C:", this.current);
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
        const key = entryKey(entry);
        return {
            "pf-m-current": key === this.current,
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
        const current = { "pf-m-current": this.current === entryKey(entry) };

        return html` <div class="pf-c-nav__link  ${classMap(current)}">
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
        const current = { "pf-m-current": this.current === entryKey(entry) };
        const path = `${entry.attributes?.isAbsoluteLink ? "" : "#"}${entry.path}`;
        return html` <div class="pf-c-nav__link ${classMap(current)}">
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
