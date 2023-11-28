import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/sidebar/SidebarBrand";
import "@goauthentik/elements/sidebar/SidebarItems";
import "@goauthentik/elements/sidebar/SidebarUser";

import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { UiThemeEnum } from "@goauthentik/api";

import { sidebarStyles } from "./Sidebar.css.js";
import type { SidebarEntry } from "./types";

@customElement("ak-sidebar")
export class Sidebar extends AKElement {
    @property({ type: Array })
    entries: SidebarEntry[] = [];

    static get styles() {
        return sidebarStyles;
    }

    render() {
        return html`<nav
            class="pf-c-nav ${this.activeTheme === UiThemeEnum.Light ? "pf-m-light" : ""}"
            aria-label="Global"
        >
            <ak-sidebar-brand></ak-sidebar-brand>
            <ak-sidebar-items .entries=${this.entries}></ak-sidebar-items>
            <ak-sidebar-user></ak-sidebar-user>
        </nav>`;
    }
}
