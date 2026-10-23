import { SidebarReloadController } from "./SidebarReloadController";
import type { SidebarItem } from "./types";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

import { AKElement } from "#elements/Base";
import Styles from "#elements/sidebar/Sidebar.css";
import { ifPresent } from "#elements/utils/attributes";

import { SlotController } from "@patternfly/pfe-core/controllers/slot-controller.js";
import { kebabCase } from "change-case";

import { msg, str } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

const slugify = (s: string) => kebabCase(s, { suffixCharacters: "-" });

@customElement("ak-sidebar")
export class Sidebar extends AKElement {
    static readonly styles = [PFPage, PFNav, Styles];

    @property({ type: Boolean })
    hidden = false;

    @property({ type: Array })
    entries: SidebarItem[] = [];

    @property({ type: String })
    current: string | null = null;

    public expanded: Map<string, boolean> = new Map();

    protected slots = new SlotController(this, {
        slots: [null, "footer"],
    });

    protected sidebarController = new SidebarReloadController(this);

    willUpdate(changed: PropertyValues<this>) {
        if (changed.has("current")) {
            const old = changed.get("current");

            if (typeof old === "string" && typeof this.current === "string") {
                this.expanded.set(old, false);
                this.expanded.set(this.current, true);
            }
        }
    }

    renderLevel2 = (entry: SidebarItem) => {
        const { path, label, key, notice } = entry;
        const current = key === this.current;

        return html`<li
            part="lever2 list-item"
            role="presentation"
            aria-label=${ifPresent(label)}
            class="pf-c-nav__item"
        >
            ${
                path
                    ? html` <a
                          part="link ${this.current ? "current" : ""}"
                          id="sidebar-nav-link-${slugify(key ?? path ?? label)}"
                          href="${path}"
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
    };

    renderLevel1 = (entry: SidebarItem) => {
        const { path, label, key, children } = entry;

        if (!children || !key || children.length === 0) {
            return nothing;
        }

        const open = this.expanded.get(key);

        return html`
            <li
                part="level1 list-item list-item-expandable"
                aria-label=${label}
                class="pf-c-nav__item pf-m-expandable ${classMap({ "pf-m-expanded": Boolean(open) })}"
                data-value=${ifPresent(key)}
            >
                ${path ? nothing : label}
                <button
                    part="button button-with-children"
                    class="pf-c-nav__link"
                    aria-label=${open ? msg(str`Collapse ${label}`) : msg(str`Expand ${label}`)}
                    aria-expanded=${open ? "true" : "false"}
                    aria-controls=${ifPresent(key)}
                    type="button"
                >
                    ${path ? label : nothing}
                    <span class="pf-c-nav__toggle">
                        <span class="pf-c-nav__toggle-icon">
                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                        </span>
                    </span>
                </button>
                <div class="pf-c-nav__subnav" ?hidden=${!open}>
                    <ul
                        role="navigation"
                        aria-label=${msg(str`${label} navigation`)}
                        class="pf-c-nav__list"
                    >
                        ${children.map(this.renderLevel2)}
                    </ul>
                </div>
            </li>
        `;
    };

    render(): TemplateResult {
        return html`<nav aria-label=${msg("Global navigation")} part="nav" class="pf-c-nav">
            <ul
                id="global-nav"
                ?hidden=${this.hidden}
                role="navigation"
                class="pf-c-nav__list ak-m-thin-scrollbar ak-m-scroll-shadows"
                part="list"
            >
                ${this.entries.map(this.renderLevel1)}
            </ul>
            <div ?hidden=${!this.slots.hasSlotted("footer")} part="footer">
                <slot name="footer"></slot>
            </div>
        </nav>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar": Sidebar;
    }
}
