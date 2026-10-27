import { SidebarReloadController } from "./SidebarReloadController";
import {
    SidebarItemWithBoth,
    SidebarItemWithPath,
    type SidebarItem,
    type SidebarItemWithChildren,
} from "./types";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

import { AKElement } from "#elements/Base";
import Styles from "#elements/sidebar/Sidebar.css";
import { ifPresent } from "#elements/utils/attributes";

import { SlotController } from "@patternfly/pfe-core/controllers/slot-controller.js";
import { kebabCase } from "change-case";
import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

const slugify = (s: string) => kebabCase(s, { suffixCharacters: "-" });

const mkIcon = (s?: string) =>
    s ? html`<i part="waypoint-icon" class=${s} aria-hidden="true"></i>` : null;

const PSidebar = { label: P.string, key: P.string };
const PSidebarArray = P.array(PSidebar);
const PBoth = { path: P.string, children: PSidebarArray };
const PPath = { path: P.string };
const PKids = { children: PSidebarArray };

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

/**
 * @element ak-sidebar
 *
 * The sidebar is a navigational element meant to assist users in finding their way about a complex
 * application.  It is
 */

@customElement("ak-sidebar")
export class Sidebar extends AKElement {
    static readonly styles = [Styles];

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

    protected renderPath({ key, label, path, notice, icon }: SidebarItemWithPath, depth = 0) {
        const current = key === this.current;
        const waypoint = mkIcon(icon);

        return html`<li part="list-item with-path" data-key=${key}>
            <a
                id="sidebar-nav-link-${slugify(key)}"
                part="row ${current ? "link current" : ""}"
                href=${path!}
                data-depth=${depth}
                aria-current=${ifPresent(current ? "page" : undefined)}
                ><div part="${waypoint ? "icon" : "rail"}">${waypoint ?? nothing}</div>
                <span part="label"
                    >${label}${
                        notice
                            ? html`<span part="notice" class="ak-c-nav__notice">${notice}</span>`
                            : nothing
                    }</span
                >
            </a>
        </li>`;
    }

    protected renderWithChildren(entry: SidebarItemWithChildren, depth = 0) {
        const { key, label, icon, children } = entry;

        const open = this.#isOpen(entry);
        const id = slugify(key);
        const waypoint = mkIcon(icon);

        return html`<li
                class="pf-m-expandable ${classMap({ "pf-m-expanded": open })}"
                part="list-item list-item-expandable"
                data-key=${key}
            >
                <button
                    id="sidebar-toggle-${id}"
                    type="button"
                    part="button row"
                    data-depth=${depth}
                    aria-expanded=${open ? "true" : "false"}
                    aria-controls="sidebar-subnav-${id}"
                    @click=${() => this.#toggleExpanded(key, !open)}
                >
                    <div part="waypoint ${icon ? "icon" : "rail"}">${waypoint}</div>
                    <span part="label">${label}</span>
                    <span part="toggle">
                        <span part="toggle-icon">
                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                        </span>
                    </span>
                </button>
            </li>
            ${open ? children.map((child) => this.renderItem(child, depth + 1)) : nothing} `;
    }

    protected renderPathAndChildren(entry: SidebarItemWithBoth, depth = 0) {
        const { key, label, icon, children } = entry;

        const open = this.#isOpen(entry);
        const id = slugify(key);
        const waypoint = mkIcon(icon);

        return html`<li
                class="pf-m-expandable ${classMap({ "pf-m-expanded": open })}"
                part="list-item list-item-expandable"
                data-key=${key}
            >
                <button id="sidebar-toggle-${id}" type="button" part="button" data-depth=${depth}>
                    <div part="waypoint ${icon ? "icon" : "rail"}">${waypoint}</div>
                    <span part="label">${label}</span>
                </button>
                <span
                    class="pf-c-nav__toggle"
                    aria-expanded=${open ? "true" : "false"}
                    aria-controls="sidebar-subnav-${id}"
                    @click=${() => this.#toggleExpanded(key, !open)}
                >
                    <span class="pf-c-nav__toggle-icon">
                        <i class="fas fa-angle-right" aria-hidden="true"></i>
                    </span>
                </span>
            </li>
            ${open ? children.map((child) => this.renderItem(child, depth + 1)) : nothing} `;
    }

    protected renderItem(entry: SidebarItem, depth = 0): TemplateResult {
        // prettier-ignore
        return match(entry)
            .with(PBoth, ({ path, children }) => this.renderPathAndChildren({ ...entry, path, children }, depth))
            .with(PKids, ({ children }) => this.renderWithChildren({ ...entry, children }, depth))
            .with(PPath, ({ path }) => this.renderPath({ ...entry, path }, depth))
            .otherwise(() => {
            console.log(entry);

                throw new Error("Sidebar entry without path or children should not happen.");
        });
    }

    render(): TemplateResult {
        return html`<nav aria-label=${msg("Global navigation")} part="nav">
            <ul
                part="nav-list"
                class="ak-m-thin-scrollbar ak-m-scroll-shadows"
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
