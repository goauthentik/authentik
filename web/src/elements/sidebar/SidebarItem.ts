import { ROUTE_SEPARATOR } from "#common/constants";

import { AKElement } from "#elements/Base";
import Styles from "#elements/sidebar/SidebarItem.css";
import { ifPresent } from "#elements/utils/attributes";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

export interface SidebarItemProperties {
    path?: string | null;
    activeWhen?: string[];
    expanded?: boolean | null;
}

@customElement("ak-sidebar-item")
export class SidebarItem extends AKElement {
    static styles: CSSResult[] = [
        // ---
        PFPage,
        PFNav,
        Styles,
    ];

    @property({ type: String })
    public path: string | null = null;

    @property({ type: String })
    public label: string | null = null;

    activeMatchers: RegExp[] = [];

    @property({ type: Boolean, useDefault: false })
    public expanded = false;

    @property({ type: Boolean, useDefault: false })
    public current = false;

    @property({ type: Boolean, attribute: "absolute-link", useDefault: false })
    public isAbsoluteLink = false;

    @property({ type: Boolean, useDefault: false })
    public highlight = false;

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

    public updated(changedProperties: PropertyValues): void {
        const previousExpanded = changedProperties.get("expanded");

        if (typeof previousExpanded !== "boolean") return;

        if (this.expanded && this.expanded !== previousExpanded) {
            cancelAnimationFrame(this.#scrollAnimationFrame);

            this.#scrollAnimationFrame = requestAnimationFrame(this.#scrollIntoView);
        }
    }

    #listRef = createRef<HTMLLIElement>();
    #scrollBehavior?: ScrollBehavior;
    #scrollAnimationFrame = -1;

    #scrollIntoView = (): void => {
        this.#listRef.value?.scrollIntoView({
            behavior: this.#scrollBehavior ?? "instant",
            block: "nearest",
        });

        this.#scrollBehavior ??= "smooth";
    };

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
            part="list-item-expandable"
            aria-label=${ifPresent(this.label)}
            role="heading"
            ${ref(this.#listRef)}
            class="pf-c-nav__item pf-m-expandable ${this.expanded ? "pf-m-expanded" : ""}"
        >
            <button
                part="button button-with-children"
                class="pf-c-nav__link"
                aria-label=${this.expanded
                    ? msg(str`Collapse ${this.label}`)
                    : msg(str`Expand ${this.label}`)}
                aria-expanded=${this.expanded ? "true" : "false"}
                aria-controls="subnav-${this.path}"
                type="button"
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
            part="list-item"
            role="presentation"
            aria-label=${ifPresent(this.label)}
            class="pf-c-nav__item pf-m-expandable ${this.expanded ? "pf-m-expanded" : ""}"
        >
            ${this.label}
            <button
                aria-label=${this.expanded
                    ? msg(str`Collapse ${this.label}`)
                    : msg(str`Expand ${this.label}`)}
                part="button button-with-path-and-children"
                class="pf-c-nav__link"
                aria-expanded=${this.expanded ? "true" : "false"}
                type="button"
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
                part="link ${this.current ? "current" : ""}"
                id="sidebar-nav-link-${this.path}"
                href="${this.isAbsoluteLink ? "" : "#"}${this.path}"
                class="pf-c-nav__link ${this.current ? "pf-m-current" : ""}"
                aria-current=${ifPresent(this.current ? "page" : undefined)}
            >
                ${this.label}
            </a>
        `;
    }

    renderWithLabel() {
        return html` <span class="pf-c-nav__link"> ${this.label}</span> `;
    }

    renderInner() {
        if (this.childItems.length > 0) {
            return this.path ? this.renderWithPathAndChildren() : this.renderWithChildren();
        }

        return html`<li
            part="list-item"
            role="presentation"
            aria-label=${ifPresent(this.label)}
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
