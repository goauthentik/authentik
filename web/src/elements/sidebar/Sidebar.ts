import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

import { AKElement } from "#elements/Base";
import Styles from "#elements/sidebar/Sidebar.css";
import { SidebarReloadController } from "#elements/sidebar/SidebarReloadController";
import type { SidebarItem } from "#elements/sidebar/types";
import { ifPresent } from "#elements/utils/attributes";

import { SlotController } from "@patternfly/pfe-core/controllers/slot-controller.js";
import { kebabCase } from "change-case";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

const slugify = (s: string) => kebabCase(s, { suffixCharacters: "-" });

export function findParentKeys(entries: readonly SidebarItem[], key: string): string[] | null {
    for (const entry of entries) {
        // Recursion end-state: We're not actually looking for the key we passed in. We know that
        // one already.
        if (entry.key === key) {
            return [];
        }

        const found = entry.children ? findParentKeys(entry.children, key) : null;

        if (found) {
            return [entry.key, ...found];
        }
    }

    return null;
}

@customElement("ak-sidebar")
export class Sidebar extends AKElement {
    static readonly styles = [PFPage, PFNav, Styles];

    @property({ type: Boolean })
    hidden = false;

    @property({ type: Array })
    entries: SidebarItem[] = [];

    /** The {@linkcode SidebarItem.key} */
    @property({ type: String })
    current: string | null = null;

    public expanded: Map<string, boolean> = new Map();

    protected slots = new SlotController(this, {
        slots: [null, "footer"],
    });

    // Optional; delete or comment out and the sidebar still works, it just doesn't remember it's
    // settings on reload.
    protected sidebarController = new SidebarReloadController(this);

    #scrollTarget: string | null = null;
    #scrollBehavior: ScrollBehavior = "instant";

    #isOpen({ key, expanded }: SidebarItem) {
        return this.expanded.get(key) ?? expanded ?? false;
    }

    #toggleExpanded(key: string, open: boolean) {
        this.expanded.set(key, open);

        if (open) {
            this.#scrollTarget = key;
        }

        this.requestUpdate();
    }

    public override willUpdate(changed: PropertyValues<this>) {
        super.willUpdate(changed);

        if (changed.has("current") && this.current) {
            for (const key of findParentKeys(this.entries, this.current) ?? []) {
                this.expanded.set(key, true);
            }

            this.#scrollTarget = this.current;
        }
    }

    get scrollTarget() {
        return this.#scrollTarget
            ? this.renderRoot.querySelector(`[data-key="${CSS.escape(this.#scrollTarget)}"]`)
            : null;
    }

    protected renderLink({ key, label, path, notice }: SidebarItem) {
        const current = key === this.current;

        return html`<li class="pf-c-nav__item" part="list-item" data-key=${key}>
            ${
                path
                    ? html` <a
                          id="sidebar-nav-link-${slugify(key)}"
                          part=${current ? "link current" : ""}
                          href=${path}
                          class="pf-c-nav__link ${classMap({ "pf-m-current": current })}"
                          aria-current=${ifPresent(current ? "page" : undefined)}
                      >
                          ${label}
                          ${
                              notice
                                  ? html`<span part="notice" class="pf-c-nav__notice"
                                        >${notice}</span
                                    >`
                                  : nothing
                          }
                      </a>`
                    : html`<span class="pf-c-nav__link"> ${label}</span>`
            }
        </li>`;
    }

    protected renderItem(entry: SidebarItem): TemplateResult {
        const { key, label, children } = entry;

        if (!children?.length) {
            return this.renderLink(entry);
        }

        const open = this.#isOpen(entry);
        const id = slugify(key);

        return html`<li
            class="pf-c-nav__item pf-m-expandable ${classMap({ "pf-m-expanded": open })}"
            part="list-item list-item-expandable"
            data-key=${key}
        >
            <button
                id="sidebar-toggle-${id}"
                type="button"
                class="pf-c-nav__link"
                part="button"
                aria-expanded=${open ? "true" : "false"}
                aria-controls="sidebar-subnav-${id}"
                @click=${() => this.#toggleExpanded(key, !open)}
            >
                ${label}
                <span class="pf-c-nav__toggle">
                    <span class="pf-c-nav__toggle-icon">
                        <i class="fas fa-angle-right" aria-hidden="true"></i>
                    </span>
                </span>
            </button>
            <div id="sidebar-subnav-${id}" class="pf-c-nav__subnav" ?hidden=${!open}>
                <ul class="pf-c-nav__list" aria-labelledby="sidebar-toggle-${id}">
                    ${children.map((child) => this.renderItem(child))}
                </ul>
            </div>
        </li>`;
    }

    render(): TemplateResult {
        return html`<nav aria-label=${msg("Global navigation")} part="nav" class="pf-c-nav">
            <ul
                part="list"
                class="pf-c-nav__list ak-m-thin-scrollbar ak-m-scroll-shadows"
                ?hidden=${this.hidden}
            >
                ${this.entries.map((entry) => this.renderItem(entry))}
            </ul>
            <div ?hidden=${!this.slots.hasSlotted("footer")} part="footer">
                <slot name="footer"></slot>
            </div>
        </nav>`;
    }

    public override updated(changed: PropertyValues<this>) {
        super.updated(changed);

        if (this.scrollTarget) {
            this.scrollTarget.scrollIntoView({ block: "nearest", behavior: this.#scrollBehavior });
            this.#scrollTarget = null;
            this.#scrollBehavior = "smooth";
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar": Sidebar;
    }
}
