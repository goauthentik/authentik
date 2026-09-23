import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

import { AKElement } from "#elements/Base";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { WithLicenseSummary } from "#elements/mixins/license";
import {
    currentInterfacePath,
    toAdminInterface,
    toCurrentInterface,
} from "#elements/router/core/interfaces";
import { RouterNavigateEvent } from "#elements/router/core/navigation";
import { readSidebarExpansion, writeSidebarExpansion } from "#elements/sidebar/expansion";
import Styles from "#elements/sidebar/SidebarItem.css";
import { ifPresent } from "#elements/utils/attributes";

import { CapabilitiesEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

export interface SidebarItemProperties {
    path?: string | null;
    key?: string | null;
    activeWhen?: string[];
    expanded?: boolean | null;
    enterprise?: boolean;
}

@customElement("ak-sidebar-item")
export class SidebarItem extends WithCapabilitiesConfig(WithLicenseSummary(AKElement)) {
    protected static instanceCount = 0;

    public static styles: CSSResult[] = [
        // ---
        PFPage,
        PFNav,
        Styles,
    ];

    @property({ type: String })
    public path: string | null = null;

    @property({ type: String })
    public label: string | null = null;

    /**
     * Stable identity for persisting this group's expansion across reloads.
     *
     * Group entries have no `path`, and their labels are translated, so neither
     * survives as a storage key. Set this explicitly on any group whose open or
     * closed state should be remembered; a group without one still expands and
     * collapses, it just starts from its declared default every load.
     */
    @property({ type: String })
    public key: string | null = null;

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

    /**
     * Per-instance id for the `aria-controls`/`id` pair.
     */
    #subnavID = `sidebar-subnav-${++SidebarItem.instanceCount}`;

    @property({ type: Boolean })
    public enterprise = false;

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

    public get activeWhen(): RegExp[] {
        return this.activeMatchers;
    }

    /**
     * @returns Key this item or `null` when it should not be remembered.
     */
    get #persistenceKey(): string | null {
        return this.key ?? this.path;
    }

    #toggleExpanded = (): void => {
        this.expanded = !this.expanded;

        if (this.#persistenceKey) {
            writeSidebarExpansion(this.#persistenceKey, this.expanded);
        }
    };

    public override connectedCallback(): void {
        super.connectedCallback();

        // Restore before synchronizing so that a group containing the active
        // route still ends up expanded even if it was collapsed by hand.
        // The matching descendant connects after us and expands its ancestors.
        const persisted = this.#persistenceKey ? readSidebarExpansion(this.#persistenceKey) : null;

        if (persisted !== null) {
            this.expanded = persisted;
        }

        window.addEventListener(RouterNavigateEvent.eventName, this.synchronize);
        window.addEventListener("popstate", this.synchronize);

        this.synchronize();
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();

        window.removeEventListener(RouterNavigateEvent.eventName, this.synchronize);
        window.removeEventListener("popstate", this.synchronize);

        cancelAnimationFrame(this.#scrollAnimationFrame);
    }

    protected override updated(changedProperties: PropertyValues): void {
        super.updated(changedProperties);

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

    /**
     * Expands all ancestor sidebar items until a deeply loaded active leaf is visible.
     *
     * This intentionally walks the light DOM (`parentElement` + `closest`) instead
     * of using {@linkcode parent}. The `parent` field is populated only after an
     * ancestor reads {@linkcode childItems}.
     *
     * On initial loads, ancestors can connect before this item exists, so that linkage may not be
     * set yet.
     */
    #expandAncestors(): void {
        let ancestor = this.parentElement?.closest<SidebarItem>("ak-sidebar-item");

        while (ancestor) {
            ancestor.expanded = true;
            ancestor = ancestor.parentElement?.closest<SidebarItem>("ak-sidebar-item");
        }
    }

    public synchronize = (): void => {
        const activePath = currentInterfacePath();

        this.current = this.matchesPath(activePath);

        if (this.current) {
            this.#expandAncestors();
        }

        this.childItems.forEach((item) => {
            this.expandParentRecursive(activePath, item);
        });
    };

    private matchesPath(path: string): boolean {
        if (!this.path) {
            return false;
        }

        const pathIsWholePath = this.path === path;
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
                aria-label=${
                    this.expanded
                        ? msg(str`Collapse ${this.label}`)
                        : msg(str`Expand ${this.label}`)
                }
                aria-expanded=${this.expanded ? "true" : "false"}
                aria-controls=${this.#subnavID}
                type="button"
                @click=${this.#toggleExpanded}
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
                    id=${this.#subnavID}
                    role="navigation"
                    aria-label=${msg(str`${this.label} navigation`)}
                    class="pf-c-nav__list"
                >
                    <slot></slot>
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
                aria-label=${
                    this.expanded
                        ? msg(str`Collapse ${this.label}`)
                        : msg(str`Expand ${this.label}`)
                }
                part="button button-with-path-and-children"
                class="pf-c-nav__link"
                aria-expanded=${this.expanded ? "true" : "false"}
                type="button"
                @click=${this.#toggleExpanded}
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

    renderEnterpriseRequired() {
        return html`<a href=${toAdminInterface("enterprise/licenses")} class="pf-c-nav__link">
            ${this.label}
            <span class="pf-c-nav__enterprise-notice">${msg("Enterprise only")}</span>
        </a>`;
    }

    renderWithPath() {
        if (this.enterprise && !this.hasEnterpriseLicense) {
            if (!this.can(CapabilitiesEnum.IsEnterprise)) return nothing;

            return this.renderEnterpriseRequired();
        }

        return html`
            <a
                part="link ${this.current ? "current" : ""}"
                id="sidebar-nav-link-${this.path}"
                href="${
                    this.isAbsoluteLink ? (this.path ?? "") : toCurrentInterface(this.path ?? "")
                }"
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
